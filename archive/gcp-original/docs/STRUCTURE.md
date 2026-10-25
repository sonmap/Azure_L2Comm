# L2Comm03-01 저장소 구조

| 경로 | 실행 위치 | 내용 |
|---|---|---|
| `gcloud/00-env.sh` | VM에서 source | 프로젝트·CIDR·SA·03-01 저장소·트리거 설정 |
| `gcloud/00-bootstrap.sh` | Owner | API와 IAM |
| `gcloud/10-network.sh` | Owner | Shared VPC·서브넷 |
| `gcloud/05-check-permissions.sh` | 배포 주체 | 권한 점검 |
| `gcloud/20-source-connection.sh` | 배포 주체 | GitHub 03-01 연결 |
| `gcloud/30-platform.sh` | 배포 주체 | AR·SA·GKE·KSA·트리거 |
| `gcloud/11-firewall.sh` | Owner | NFS 및 Control Plane 통신 |
| `gcloud/99-verify.sh` | 조회 주체 | 자원과 Pod 상태 확인 |
| `gcloud/90-teardown.sh` | 배포 주체 | 공유 인프라 삭제용. 재테스트 시 실행 불필요 |
| `app/` | Cloud Build / Pod | 이미지 내부 `/app/main.py` 적재 샘플 |
| `cloudbuild/cloudbuild.yaml` | Cloud Build | 이미지 빌드와 Host AR 업로드 |
| `ssw/dlk/install-vm.sh` | VM | `/ssw/dlk` 심볼릭 링크 최초 생성 |
| `ssw/dlk/setup-nfs-server.sh` | VM sudo | 현재 체크아웃의 `mnt/`를 NFS로 export |
| `ssw/dlk/client_common` | VM에서 source | RSVP 환경변수 |
| `ssw/dlk/run-gke.sh` | VM | 9개 필수 인자 및 이후 프로그램 인자를 client_gke에 전달 |
| `ssw/dlk/client_gke` | VM | PV/PVC·Pod YAML 생성, apply, Succeeded 대기, 로그, 성공 Pod 삭제 |
| `mnt/batch_gke/l2_gke_sh/rsvp/GP_L2RSVP_001_1/run-gke.sh` | VM | RSVP 실행 래퍼 |
| `mnt/batch_gke/l2/rsvp/GP_L2RSVP_001_1/python/bq_auth_smoke.py` | Pod | BigQuery 키 인증 검사 |
| `mnt/python/bq_sample.py` | Pod (별도 export 설정 필요) | 기존 테이블 조회 |
| `helm/l2comm-batch/`, `k8s/debug-pod.yaml` | 참고 | RSVP 표준 실행과 별도 설정 |
| `docs/RUNBOOK.md` | 사람 | 단계별 실행과 기대 결과 |

RSVP 마운트 매핑:

| VM | Pod |
|---|---|
| `~/Gcp_Managed_GKE_L2Comm03-01/mnt/batch_gke/l2/rsvp/` | `/home/jupyter/` |
| `.../rsvp/.oefj` | `/home/jupyter/.oefj` |
| `.../rsvp/GP_L2RSVP_001_1/python/` | `/home/jupyter/GP_L2RSVP_001_1/python/` |

기본 NFS 하위 경로가 RSVP이므로 `mnt/python/`는 이 마운트에 나타나지 않습니다.
기존 `/ssw/dlk` 링크를 바꾼 뒤 NFS bind mount도 새 체크아웃으로 갱신해야 합니다.
`install-vm.sh`는 `REPOINT=true`를 지원하지 않으며, 상세 절차는 RUNBOOK §10-1을 따릅니다.
성공한 배치는 Pod를 삭제합니다. 실패 Pod는 이름을 확인한 뒤 수동 점검합니다.
