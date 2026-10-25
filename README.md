# Azure_L2Comm

기존 [GCP L2Comm03-01](https://github.com/sonmap/Gcp_Managed_GKE_L2Comm03-01)을 Azure에 이식한 PoC 구성이다.

**[Azure CLI RUNBOOK](docs/RUNBOOK.md)** | [구성·권한 비교](docs/DESIGN.md) | [검증 결과](docs/VALIDATION.md)

| 원본 GCP | Azure 구성 |
|---|---|
| Shared VPC Host | 네트워크 RG + 공통 VNet·서브넷 |
| GKE Autopilot | Private AKS Standard + system/user node pool + autoscaler |
| GKE Service Agent | AKS Control Plane Managed Identity |
| Node SA / AR Reader | kubelet identity / ACR AcrPull |
| Artifact Registry / Cloud Build | Azure Container Registry / ACR Tasks |
| 생성 VM | l2comn-dev, Azure CLI 실행 |
| Edge VM / NFS | central02, Git·배치 실행·NFS |
| run-gke.sh / client_gke | 호환 wrapper → run-aks.sh / client_aks |
| .oefj / BigQuery | 기존 GCP 업무 인증·테스트 유지 |

- 인프라 명령은 문서에서 직접 실행한다. 자동 인프라 sh를 새로 만들지 않는다.
- 두 VM에 Git 소스를 배치하고 NFS와 mnt bind mount는 central02만 구성한다.
- 기존 업무별 run-gke.sh 인자와 /home/jupyter 마운트를 유지한다.
- Node/Pod 대역은 Azure 예약 IP·Overlay /24 노드 할당 기준으로 재설계했다.
- 기본안은 한 구독, 네 RG, NAT Gateway, Private AKS API, RBAC ACR, 일반 VM NFS다.
- AKS Standard는 Autopilot과 다르며 system 노드 및 최소 용량 비용이 발생한다.
- Azure에 리소스를 실제 생성하지 않았다. 구독·Object ID·고유 ACR명은 사용자 입력이 필요하다.
- 원본 35개 파일은 archive/gcp-original에 보존했다. 참고용이며 실행 대상이 아니다.
- .oefj·비밀키·로그인 토큰은 포함하지 않는다.

```bash
git clone https://github.com/sonmap/Azure_L2Comm.git
cd Azure_L2Comm
```
