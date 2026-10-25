# L2Comm03-01 설계

## 프로젝트 및 네트워크

| 항목 | 값 |
|---|---|
| Host / Artifact Registry | `gcp-prod-edp-hub-vpchost` |
| Edge / GKE / Cloud Build | `gcp-prod-edp-edge-509423` |
| BigQuery 데이터 | `pjt-c-admin` |
| VPC | `vpc-prod-edp-hub` |
| 서브넷 | `subnet-prod-edp-l2comm-gke-an3` |
| Node Primary | `10.252.1.0/24` |
| Pod Secondary | `100.64.128.0/19` |
| Control Plane | `10.254.5.0/28` |
| Service | GKE 관리 대역 (서브넷에 별도 생성하지 않음) |
| 클러스터 | `gke-l2comm-batch-an3`, `asia-northeast3` |

인프라 이름은 03과 공유합니다. 03-01은 별도 클러스터를 의미하지 않습니다.

## 빌드 및 실행

Cloud Build의 `Gcp_Managed_GKE_L2Comm03-01` 연결과
`trg-l2comm03-01-python-image` 트리거가 `app/`, `cloudbuild/`, `gcloud/` 변경을 빌드합니다.
이미지는 Host 프로젝트의 `ar-l2comm-python/python-bq-batch:v1`에 저장됩니다.
기존 03도 같은 이미지 태그를 사용하므로 빌드 시 공유 태그가 갱신됩니다.

실행은 VM → RSVP run-gke.sh → 공통 run-gke.sh → client_gke → GKE Pod 방식입니다.
Pod는 NFS의 `/batch_gke/l2/rsvp`를 `/home/jupyter`에 읽기 전용 마운트합니다.
인증 샘플은 `/home/jupyter/.oefj`를 명시적으로 읽습니다.
플랫폼의 `sa-l2comm-gke` 및 KSA Workload Identity 구성과 키 인증 검사는 구분합니다.
`client_gke`는 KSA→GSA 어노테이션을 설정하지 않습니다. BigQuery Python 클라이언트는 `.oefj`에서 만든 credentials를 명시적으로 사용합니다.

DRY_RUN 기본값은 1입니다. 0일 때 PV/PVC와 Pod를 적용합니다.
클라이언트는 최대 3600초 동안 Succeeded를 기다리고 로그를 출력합니다.
성공 Pod는 삭제하고 실패 Pod는 남깁니다. Job 재시도나 TTL은 없습니다.

## 계정과 접근

Owner `admin@sonmap.net`은 IAM·네트워크·방화벽을 관리합니다.
배포 주체 `cho@sonmap.net`은 권한 점검 이후 플랫폼을 구성합니다.
VM의 kubectl 인증 주체가 GKE API에 Pod와 PV/PVC를 생성할 권한이 있어야 합니다.
키 파일의 서비스 계정은 BigQuery 쿼리 실행 프로젝트에 Job User 권한이 필요합니다.
`bq_auth_smoke.py`는 테이블 없이 상수 SELECT만 실행합니다.
`app/main.py`는 동일한 `.oefj` 키로 Compute 리전을 조회해 테이블을 덮어쓰는 별도 샘플입니다.

키 파일은 Git 관리 대상에서 제외하며 기존 VM 파일을 별도로 준비합니다.
Private endpoint, NFS TCP 2049, 이미지 Pull 접근은 RUNBOOK에서 순서대로 확인합니다.
