# Azure L2Comm 실행 절차

원본: sonmap/Gcp_Managed_GKE_L2Comm03-01 (tree 5d620b0061c7e0dc013a2fa38b21a2052e058736).
실제 Azure에 배포하지 않은 구성·명령 문서다. 구독·테넌트·계정 Object ID·전역 고유 ACR 이름을 입력한 뒤 실행한다.
인프라는 개별 az 명령으로 구성하고 NFS만 sh를 사용한다. 기존 업무 run-gke.sh는 호환 진입점으로 유지한다.
각 명령 출력과 기존 리소스를 확인하며 진행한다. 기존 자원의 create나 역할 중복 오류를 무시하지 않는다.

## 0. 설계와 입력값

동일 테넌트·동일 구독에 네 Resource Group을 사용하는 기본 PoC다.
GCP 프로젝트를 Azure 구독 네 개로 자동 매핑하지 않는다. 교차 구독은 별도 권한·provider 등록 검토가 필요하다.
GKE Autopilot과 AKS Standard는 동일 제품이 아니다. AKS system/user pool과 autoscaler를 명시적으로 관리한다.
Private AKS API + Azure CNI Overlay, VM 기반 NFS, ACR RBAC 모드를 사용한다.
ACR은 기본안에서 공개 서비스 Endpoint로 NAT를 통해 접근한다. ACR Private Link·완전 인터넷 차단 구성은 아니다.
Azure CLI 설치·Azure 로그인·리소스 생성만으로 BigQuery를 Azure 서비스로 변환하지 않는다. .oefj/BQ 로직은 유지한다.

| 역할 | 기본 리소스 그룹 | 담당 |
|---|---|---|
| 네트워크 | rg-l2comm-network | network_admin |
| Edge / ACR / NFS | rg-l2comm-edge | edge_admin |
| AKS / 관리 ID | rg-l2comm-aks | aks_admin |
| 생성 VM | rg-l2comm-management | aks_admin |

사용자 역할은 실제 Entra Object ID로 입력한다. 담당자 이메일·GUID·구독을 추정하지 않는다.
AAD/Entra tenant 설정과 정책이 다르면 먼저 조정한다.

```bash
export SUBSCRIPTION_ID="<Azure subscription GUID>"
export TENANT_ID="<Microsoft Entra tenant GUID>"
export NETWORK_ADMIN_OID="<network_admin user Object ID>"
export EDGE_ADMIN_OID="<edge_admin user Object ID>"
export AKS_ADMIN_OID="<aks_admin user Object ID>"
export LOCATION="koreacentral"
export NET_RG="rg-l2comm-network"
export EDGE_RG="rg-l2comm-edge"
export AKS_RG="rg-l2comm-aks"
export VM_RG="rg-l2comm-management"
export VNET="vnet-l2comm"
export VNET_CIDR="10.253.0.0/16"
export NODE_SUBNET="snet-l2comm-node"
export NODE_CIDR="10.253.0.0/24"
export MGMT_SUBNET="snet-l2comm-management"
export MGMT_CIDR="10.253.10.0/24"
export POD_CIDR="10.244.0.0/20"
export SERVICE_CIDR="10.245.0.0/24"
export DNS_SERVICE_IP="10.245.0.10"
export NFS_SERVER="10.253.10.4"
export CREATE_VM_IP="10.253.10.5"
export SSH_SOURCE_CIDR="<approved VPN or Bastion source CIDR>"
export ACR_NAME="<globally-unique lowercase alphanumeric ACR name>"
export AKS="aks-l2comm-batch"
export CLUSTER_IDENTITY="id-l2comm-controlplane"
export LINUX_USER="azureuser"
```

모든 CIDR은 후보이며 VNet·Pod·Service·사내·VPN 중복을 사전 확인한다.
Azure 서브넷은 처음 4개와 마지막 1개 IP를 예약한다. 관리 IP .4/.5를 사용하고 기존 GCP 주소를 그대로 옮기지 않는다.
Overlay는 노드마다 /24를 할당하므로 Pod /20은 16노드분이다. system 2 + user 최대 3 + surge 여유를 확보한다.
Node /28·Pod /22를 그대로 복제하지 않는다. Service CIDR도 VNet과 중복되지 않아야 한다.
기존 VPN/ExpressRoute/Bastion 관리 경로를 전제로 하며 VM에 Public IP를 부여하지 않는다.

## 1. 공통 도구·소스 — 두 VM

Ubuntu 22.04 VM 생성 후 각각의 VM 안에서 실행한다. 최초 Azure 자원 생성은 Azure CLI가 있는 관리 단말에서 수행한다.
Azure CLI 미설치 시 공식 APT 절차:
https://learn.microsoft.com/cli/azure/install-azure-cli-linux?pivots=apt
설치에 필요한 외부 통신 경로를 확인한다.

```bash
sudo apt-get update
sudo apt-get install -y git python3 python3-venv python3-pip ca-certificates curl
az version
sudo az aks install-cli
kubectl version --client
kubelogin --version
git clone https://github.com/sonmap/Azure_L2Comm.git
cd Azure_L2Comm
```

기존 clone은 git pull --ff-only를 사용한다. Docker/Helm은 필수가 아니며 Python 업무 의존성은 app/requirements.txt로 이미지에 설치한다.

## 2. 기반 관리자 — RG·Provider·작업자 권한

RG 생성에는 구독 범위 권한, 역할 할당에는 Owner/User Access Administrator 등의 권한이 필요하다.
Contributor만으로 역할 할당은 불가하다. az login마다 계정을 확인하고 담당자별로 같은 변수를 정의한다.

```bash
az login --tenant "$TENANT_ID"
az account set --subscription "$SUBSCRIPTION_ID"
az account show --query '{subscription:id,tenant:tenantId,user:user.name}' -o table

az provider register --namespace Microsoft.ContainerService --wait
az provider register --namespace Microsoft.ContainerRegistry --wait
az provider register --namespace Microsoft.Network --wait
az provider register --namespace Microsoft.Compute --wait
az provider register --namespace Microsoft.ManagedIdentity --wait

az group create -n "$NET_RG" -l "$LOCATION"
az group create -n "$EDGE_RG" -l "$LOCATION"
az group create -n "$AKS_RG" -l "$LOCATION"
az group create -n "$VM_RG" -l "$LOCATION"

export NET_RG_ID="$(az group show -n "$NET_RG" --query id -o tsv)"
export EDGE_RG_ID="$(az group show -n "$EDGE_RG" --query id -o tsv)"
export AKS_RG_ID="$(az group show -n "$AKS_RG" --query id -o tsv)"
export VM_RG_ID="$(az group show -n "$VM_RG" --query id -o tsv)"

az role assignment create --assignee-object-id "$NETWORK_ADMIN_OID" --assignee-principal-type User --role Contributor --scope "$NET_RG_ID"
az role assignment create --assignee-object-id "$EDGE_ADMIN_OID" --assignee-principal-type User --role Contributor --scope "$EDGE_RG_ID"
az role assignment create --assignee-object-id "$AKS_ADMIN_OID" --assignee-principal-type User --role Contributor --scope "$AKS_RG_ID"
az role assignment create --assignee-object-id "$AKS_ADMIN_OID" --assignee-principal-type User --role Contributor --scope "$VM_RG_ID"
```

후속 역할 할당도 기반 권한 관리자가 실행한다. 담당자에게 Owner를 일괄 부여하지 않는다.
입력 Object ID는 사용자 기준이다. 그룹을 쓰면 principal type을 Group으로 변경한다.

## 3. network_admin — VNet·명시적 Egress·NSG

암묵적인 외부 연결을 전제로 하지 않는다. AKS와 관리 VM 서브넷에 NAT Gateway를 연결한다.
PoC는 NAT로 ACR/MCR/Ubuntu/GitHub/Google API에 연결한다. 엄격한 출구 제어는 Azure Firewall 등으로 별도 설계한다.

```bash
az network vnet create -g "$NET_RG" -n "$VNET" --address-prefixes "$VNET_CIDR" \
  --subnet-name "$NODE_SUBNET" --subnet-prefixes "$NODE_CIDR"
az network vnet subnet create -g "$NET_RG" --vnet-name "$VNET" -n "$MGMT_SUBNET" --address-prefixes "$MGMT_CIDR"
az network public-ip create -g "$NET_RG" -n pip-l2comm-nat --sku Standard --allocation-method Static
az network nat gateway create -g "$NET_RG" -n nat-l2comm --public-ip-addresses pip-l2comm-nat
az network vnet subnet update -g "$NET_RG" --vnet-name "$VNET" -n "$NODE_SUBNET" --nat-gateway nat-l2comm
az network vnet subnet update -g "$NET_RG" --vnet-name "$VNET" -n "$MGMT_SUBNET" --nat-gateway nat-l2comm

az network nsg create -g "$NET_RG" -n nsg-l2comm-management
az network nsg rule create -g "$NET_RG" --nsg-name nsg-l2comm-management -n allow-admin-ssh \
  --priority 100 --direction Inbound --access Allow --protocol Tcp \
  --source-address-prefixes "$SSH_SOURCE_CIDR" --destination-address-prefixes "$MGMT_CIDR" --destination-port-ranges 22
az network nsg rule create -g "$NET_RG" --nsg-name nsg-l2comm-management -n allow-aks-nfs \
  --priority 110 --direction Inbound --access Allow --protocol Tcp \
  --source-address-prefixes "$NODE_CIDR" --destination-address-prefixes "$NFS_SERVER" --destination-port-ranges 2049
az network nsg rule create -g "$NET_RG" --nsg-name nsg-l2comm-management -n deny-other-inbound \
  --priority 4000 --direction Inbound --access Deny --protocol '*' \
  --source-address-prefixes '*' --destination-address-prefixes '*' --destination-port-ranges '*'
az network vnet subnet update -g "$NET_RG" --vnet-name "$VNET" -n "$MGMT_SUBNET" --network-security-group nsg-l2comm-management

export VNET_ID="$(az network vnet show -g "$NET_RG" -n "$VNET" --query id -o tsv)"
export NODE_SUBNET_ID="$(az network vnet subnet show -g "$NET_RG" --vnet-name "$VNET" -n "$NODE_SUBNET" --query id -o tsv)"
export MGMT_SUBNET_ID="$(az network vnet subnet show -g "$NET_RG" --vnet-name "$VNET" -n "$MGMT_SUBNET" --query id -o tsv)"
```

관리 NSG는 승인된 SSH와 Node→NFS만 허용하고 우선순위 deny로 기본 AllowVNetInBound도 제한한다.
AKS Node 서브넷에는 이 관리 NSG를 연결하지 않는다. Overlay의 Node/Pod 통신을 차단하지 않도록 한다.
기존 AWS/GCP/사내망과 충돌하면 변수를 변경한 후 생성한다.

## 4. aks_admin — Control Plane Identity / 기반 관리자 — 네트워크 권한

```bash
az identity create -g "$AKS_RG" -n "$CLUSTER_IDENTITY"
export CLUSTER_MI_ID="$(az identity show -g "$AKS_RG" -n "$CLUSTER_IDENTITY" --query id -o tsv)"
export CLUSTER_MI_OID="$(az identity show -g "$AKS_RG" -n "$CLUSTER_IDENTITY" --query principalId -o tsv)"
```

다음 역할 할당은 기반 권한 관리자 담당이다. AKS가 Private DNS VNet link를 만들도록 VNet 범위의 Network Contributor를 부여한다.

```bash
az role assignment create --assignee-object-id "$CLUSTER_MI_OID" --assignee-principal-type ServicePrincipal \
  --role "Network Contributor" --scope "$VNET_ID"
az role assignment create --assignee-object-id "$AKS_ADMIN_OID" --assignee-principal-type User \
  --role "Network Contributor" --scope "$NODE_SUBNET_ID"
az role assignment create --assignee-object-id "$AKS_ADMIN_OID" --assignee-principal-type User \
  --role "Network Contributor" --scope "$MGMT_SUBNET_ID"
az role assignment create --assignee-object-id "$EDGE_ADMIN_OID" --assignee-principal-type User \
  --role "Network Contributor" --scope "$MGMT_SUBNET_ID"
```

GCP의 container-engine-robot 계정을 Azure에 만들지 않는다. Control Plane MI와 kubelet identity는 별개다.
기본안은 AKS가 Private DNS Zone을 system 방식으로 만들고 같은 VNet의 VM에서 이름을 해석한다.
커스텀 DNS 사용 시 Private DNS 전달·해석 경로는 별도 설정한다.

## 5. VM作成 — aks_admin / edge_admin

관리 VM은 OS 이미지 최소 용량에 맞춰 30GB Standard HDD를 사용한다.
20GB를 강제하지 않는다. NFS를 겸하는 central02는 가용성을 위해 일반 VM을 기본으로 사용하며 Spot으로 만들지 않는다.
이 절차에서는 백업 정책을 연결하지 않는다. 조직의 자동 백업 정책은 별도 확인한다.
기존 SSH 공개키를 지정하며 비밀키는 Git에 추가하지 않는다.

```bash
export SSH_PUBLIC_KEY="$HOME/.ssh/id_rsa.pub"

# aks_admin: provisioning client
az vm create -g "$VM_RG" -n l2comn-dev --image Ubuntu2204 \
  --size Standard_B2s --admin-username "$LINUX_USER" --ssh-key-values "$SSH_PUBLIC_KEY" \
  --subnet "$MGMT_SUBNET_ID" --private-ip-address "$CREATE_VM_IP" --public-ip-address "" \
  --nsg "" --storage-sku Standard_LRS --os-disk-size-gb 30

# edge_admin: batch client and NFS
az vm create -g "$EDGE_RG" -n central02 --image Ubuntu2204 \
  --size Standard_B2s --admin-username "$LINUX_USER" --ssh-key-values "$SSH_PUBLIC_KEY" \
  --subnet "$MGMT_SUBNET_ID" --private-ip-address "$NFS_SERVER" --public-ip-address "" \
  --nsg "" --storage-sku Standard_LRS --os-disk-size-gb 30
```

기존 VPN/Bastion을 통해 SSH한다. az vm open-port로 Public SSH를 개방하지 않는다.
두 VM 모두 1절 도구와 Git을 준비한다. NFS와 mnt bind mount는 central02에만 구성한다.

## 6. aks_admin — Private AKS作成

```bash
az aks create -g "$AKS_RG" -n "$AKS" -l "$LOCATION" \
  --tier standard --enable-managed-identity --assign-identity "$CLUSTER_MI_ID" \
  --enable-private-cluster --disable-public-fqdn --private-dns-zone system \
  --enable-aad --enable-azure-rbac --disable-local-accounts \
  --network-plugin azure --network-plugin-mode overlay \
  --vnet-subnet-id "$NODE_SUBNET_ID" --pod-cidr "$POD_CIDR" \
  --service-cidr "$SERVICE_CIDR" --dns-service-ip "$DNS_SERVICE_IP" \
  --outbound-type userAssignedNATGateway \
  --nodepool-name system --node-count 2 --node-vm-size Standard_D4s_v5 \
  --max-pods 30 --generate-ssh-keys

az aks nodepool add -g "$AKS_RG" --cluster-name "$AKS" -n batch \
  --mode User --node-vm-size Standard_E4s_v5 --node-count 1 \
  --enable-cluster-autoscaler --min-count 0 --max-count 3 --max-pods 30
```

E4s_v5는 4 vCPU/32Gi급이나 실제 allocatable은 OS·시스템 예약만큼 줄어든다.
4 CPU 요청 Pod는 4 vCPU 노드에 들어가지 못할 수 있다. 검증은 2 CPU/8Gi로 하고 4 CPU 업무는 E8s_v5 등으로 조정한다.
GPU 0 이외에는 별도 GPU 풀·Device Plugin·드라이버가 필요하다. 기본 절차에서는 GPU를 생성하지 않는다.
Korea Central의 SKU 제공·할당량·AKS 버전을 확인한다. GKE regular 채널을 그대로 대응하지 않는다.

## 7. edge_admin — ACR·빌드 / 기반 관리자 — Pull 권한

```bash
az acr create -g "$EDGE_RG" -n "$ACR_NAME" -l "$LOCATION" \
  --sku Standard --admin-enabled false --role-assignment-mode rbac

export ACR_ID="$(az acr show -g "$EDGE_RG" -n "$ACR_NAME" --query id -o tsv)"
export ACR_LOGIN_SERVER="$(az acr show -g "$EDGE_RG" -n "$ACR_NAME" --query loginServer -o tsv)"
export DOCKER_IMAGE="${ACR_LOGIN_SERVER}/python-bq-batch:v1"
export AKS_ID="$(az aks show -g "$AKS_RG" -n "$AKS" --query id -o tsv)"
export KUBELET_OID="$(az aks show -g "$AKS_RG" -n "$AKS" --query identityProfile.kubeletidentity.objectId -o tsv)"
```

역할 할당은 기반 관리자 담당이다. 다른 RG 조회에는 Reader 등이 필요하므로 담당자가 얻은 리소스 ID를 공유한다.
Registry RBAC 모드를 명시했으므로 AcrPull을 사용한다. 기존 ABAC Registry에는 그대로 적용하지 않는다.

```bash
az role assignment create --assignee-object-id "$KUBELET_OID" --assignee-principal-type ServicePrincipal \
  --role AcrPull --scope "$ACR_ID"
az role assignment create --assignee-object-id "$EDGE_ADMIN_OID" --assignee-principal-type User \
  --role "Container Registry Tasks Contributor" --scope "$ACR_ID"
az role assignment create --assignee-object-id "$EDGE_ADMIN_OID" --assignee-principal-type User \
  --role AcrPush --scope "$ACR_ID"
```

edge_admin이 Git 소스가 있는 VM에서 빌드를 제출한다. 로컬 Docker는 필요 없으며 ACR Tasks가 베이스 이미지·PyPI에 연결한다.
VM의 Linux 사용자와 az login의 Entra 사용자를 구분한다.

```bash
cd ~/Azure_L2Comm
az account show --query user.name -o tsv
az acr build -r "$ACR_NAME" -t python-bq-batch:v1 -f app/Dockerfile app
az acr repository show-tags -n "$ACR_NAME" --repository python-bq-batch -o table
```

이미지 도메인은 loginServer에서 조회한다. ACR 이름으로 도메인을 추측하지 않는다.
이미지 Pull 주체는 kubelet identity이며 KSA·Control Plane MI·.oefj SA가 아니다.

## 8. 기반 관리자 — AKS 사용자 권한

```bash
az role assignment create --assignee-object-id "$AKS_ADMIN_OID" --assignee-principal-type User \
  --role "Azure Kubernetes Service Cluster User Role" --scope "$AKS_ID"
az role assignment create --assignee-object-id "$EDGE_ADMIN_OID" --assignee-principal-type User \
  --role "Azure Kubernetes Service Cluster User Role" --scope "$AKS_ID"
az role assignment create --assignee-object-id "$AKS_ADMIN_OID" --assignee-principal-type User \
  --role "Azure Kubernetes Service RBAC Cluster Admin" --scope "$AKS_ID"
az role assignment create --assignee-object-id "$EDGE_ADMIN_OID" --assignee-principal-type User \
  --role "Azure Kubernetes Service RBAC Cluster Admin" --scope "$AKS_ID"
```

기존 client는 Namespace/KSA/PV/PVC/Pod를 생성한다. PV가 클러스터 범위이므로 PoC는 RBAC Cluster Admin을 명시한다.
운영 최소 권한화는 초기 생성자와 실행자를 분리한다. Cluster User Role은 kubeconfig 다운로드 권한이며 Pod 조작 권한과 별개다.
권한 반영에는 시간이 걸릴 수 있다. 역할 할당과 Private API의 TCP443·DNS 연결은 별개다.

## 9. central02 — NFS·기존 파일

```bash
cd ~/Azure_L2Comm
sudo mkdir -p /ssw
sudo ln -s "$PWD/ssw/dlk" /ssw/dlk
sudo env NFS_CLIENT_CIDR="$NODE_CIDR" bash ssw/dlk/setup-nfs-server.sh
findmnt /srv/l2comm-nfs
sudo exportfs -v
```

기존 /ssw/dlk가 다른 경로이면 덮어쓰지 말고 확인한다.
NFSv4.1로 repo mnt를 /srv/l2comm-nfs에 bind하고 /batch_gke/l2/rsvp를 Pod /home/jupyter에 읽기 전용 마운트한다.
기존 승인된 .oefj를 central02의 mnt/batch_gke/l2/rsvp/.oefj에 배치하고 내용을 로그로 출력하지 않는다.
키 생성·Google 조직 정책 변경·키의 Git 등록은 수행하지 않는다.

```bash
ls -l mnt/batch_gke/l2/rsvp/.oefj
ls -l /srv/l2comm-nfs/batch_gke/l2/rsvp/.oefj
namei -l /srv/l2comm-nfs/batch_gke/l2/rsvp/.oefj
git check-ignore mnt/batch_gke/l2/rsvp/.oefj
```

root_squash, Pod UID/GID의 읽기 및 상위 경로 탐색 권한을 확인한다. chmod 777은 사용하지 않는다.
NFS는 Azure Files가 아닌 VM NFS다. PV_SIZE는 실제 NFS 용량 제한을 설정하는 값이 아니다.
central02 정지 시 NFS도 정지한다. 본 운영은 Azure Files NFS/ANF 등의 가용성 설계가 별도로 필요하다.

## 10. central02 — AKS 접속·run-gke.sh 호환 실행

```bash
az login --tenant "$TENANT_ID"
az account set --subscription "$SUBSCRIPTION_ID"
export KUBECONFIG="$HOME/.kube/config_l2comm_aks"
mkdir -p "$HOME/.kube"
az aks get-credentials -g "$AKS_RG" -n "$AKS" --file "$KUBECONFIG" --overwrite-existing
kubelogin convert-kubeconfig -l azurecli
kubectl get nodes -o wide
kubectl auth can-i create persistentvolumes
kubectl auth can-i create pods -n l2comm-batch

export DOCKER_IMAGE="${ACR_LOGIN_SERVER}/python-bq-batch:v1"
export NFS_SERVER="10.253.10.4"
export NFS_PATH="/batch_gke/l2/rsvp"
export SA_KEY_PATH="/home/jupyter/.oefj"
export BQ_JOB_PROJECT="pjt-c-admin"
export DRY_RUN=1

./mnt/batch_gke/l2_gke_sh/rsvp/GP_L2RSVP_001_1/run-gke.sh \
  20261025 20261025 20261025 120000 \
  0 2 8 \
  /mnt/batch_gke/l2/rsvp/GP_L2RSVP_001_1/python \
  python bq_auth_smoke.py
```

출력 확인 후 DRY_RUN=0으로 같은 명령을 실행한다. 현재 kubeconfig가 대상 AKS인지 확인한다.
run-gke.sh → run-aks.sh → client_aks가 Pod를 직접 생성하며 Job으로 변경하지 않는다.
기존 9개 위치 인자·후속 프로그램 인자·경로 변환을 유지한다. run-aks.sh 직접 호출은 Pod 내부 경로를 사용한다.
Succeeded는 로그 후 Pod 삭제, Failed는 조기 감지 후 보존한다. POD_TIMEOUT_SECONDS 기본값은 3600초다.
GPU 인자는 원본 호환용으로 보존하며 기본 풀에서는 0을 사용한다.
BigQuery SELECT는 기존 GCP 서비스에 실행한다. Azure MI가 Google SA 키를 대체하지 않는다.
Google token/API HTTPS 연결, NAT 출구, GCP VPC-SC·조직 제약·BQ 권한을 확인한다.
Azure 네이티브 DB 전환은 별도 애플리케이션 변경이며 이번 인프라 이식에 포함되지 않는다.

## 11. 모니터링·장애 확인

```bash
kubectl get nodes -o custom-columns='NODE:.metadata.name,CPU:.status.capacity.cpu,MEM:.status.capacity.memory,MAX_PODS:.status.allocatable.pods,POD_CIDR:.spec.podCIDR'
kubectl top nodes
kubectl get pods -A -o wide
az aks show -g "$AKS_RG" -n "$AKS" --query '{private:apiServerAccessProfile.enablePrivateCluster,fqdn:privateFqdn,network:networkProfile,identity:identityProfile}' -o yaml
```

| 症状 | 確認 |
|---|---|
| Private API timeout | VPN/Bastion経路、Private DNS、NSG TCP443 |
| Unauthorized/Forbidden | az login·kubelogin·Cluster User 및 RBAC Cluster Admin |
| ImagePullBackOff not found | ACR loginServer、repository/tag |
| ImagePullBackOff 403 | kubelet identity의 AcrPull·Registry RBAC/ABAC 모드 |
| FailedMount | central02 TCP2049·NSG Node CIDR·NFS export 경로 |
| Missing or unreadable SA key | central02 키·root_squash·Pod UID/GID |
| Pending insufficient cpu | 시스템 예약 후 allocatable·요청량·pool 확장·quota |

실패 Pod 이름을 조회하고 로그 확보 후 해당 Pod만 삭제·재실행한다. PV/PVC는 유지한다.
초기 system 2 + batch 1로 3노드이며 batch 최대 3, Pod CIDR은 surge를 고려한 16노드분이다.
system pool은 기본적으로 0노드로 축소하지 않는다.

## 12. 실환경 검증 범위

저장소 구성 시 Azure 리소스를 생성하지 않았다. CLI는 공식 문서를 참고했지만 실제 테넌트에서 실행하지 않았다.
로컬 검증은 Bash 문법·Python 컴파일·DRY_RUN 매니페스트·성공/실패 모의 실행으로 한정한다.
지역 SKU·할당량·Entra 권한·Private DNS·NFS/BQ·ACR Tasks 사용 가능 여부는 배포 시 검증한다.
Azure 정책과 기존망 정합성을 우선한다. RG 일괄 삭제 teardown은 제공하지 않는다.

公式資料:
- https://learn.microsoft.com/azure/aks/private-clusters
- https://learn.microsoft.com/azure/aks/concepts-network-azure-cni-overlay
- https://learn.microsoft.com/azure/aks/use-managed-identity
- https://learn.microsoft.com/azure/aks/manage-azure-rbac
- https://learn.microsoft.com/azure/aks/kubelogin-authentication
- https://learn.microsoft.com/azure/aks/cluster-container-registry-integration
- https://learn.microsoft.com/azure/container-registry/container-registry-roles
