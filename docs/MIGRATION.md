# 원본 이식 범위

원본 tree: 5d620b0061c7e0dc013a2fa38b21a2052e058736

| 경로 | 처리 |
|---|---|
| archive/gcp-original | 원본 35개 파일 내용 보존 |
| app | 기존 Python 컨테이너·BQ 의존성 유지 |
| mnt | 기존 업무 Python과 업무별 run-gke.sh 유지 |
| ssw/dlk/run-gke.sh | 기존 이름의 Azure 호환 wrapper |
| ssw/dlk/run-aks.sh | 기존 9개 위치 인자·후속 인자 처리 재사용 |
| ssw/dlk/client_aks | 원본 PV/PVC/Pod 생성 유지, AKS 환경·실패 조기 감지 반영 |
| ssw/dlk/client_gke | client_aks 호환 wrapper |
| ssw/dlk/client_common | AKS kubeconfig 기본값, GCP 기본 이미지 제거 |
| ssw/dlk/setup-nfs-server.sh | central02 제한, export 허용 Node CIDR 필수 |
| docs/RUNBOOK.md | Azure CLI·Managed Identity·NSG·AKS·ACR 실행 순서 |
| k8s/debug-pod.yaml | ACR 이미지 입력 후 사용하는 NFS debug Pod |

기존 업무 프로그램 자체를 Azure SQL/Synapse로 변경하지 않았다. app/main.py 등 GCP 샘플은 BQ를 사용하는 원본 업무 예제로 남긴다.
Azure 통신·AKS 인증에 GCP SDK나 gcloud를 요구하지 않는다. 컨테이너의 BQ SDK는 기존 업무 의존성이다.
원본 Cloud Build와 gcloud 인프라 shell은 archive에만 존재하며 Azure 실행 절차에서 사용하지 않는다.
