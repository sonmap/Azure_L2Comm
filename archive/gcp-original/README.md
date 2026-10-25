# Gcp_Managed_GKE_L2Comm03-01

L2Comm03의 gcloud 구축 구성에 L2Comm02의 `feature/rsvp-pod-oefj-mount` 브랜치에 있는
`ssw/`, `mnt/` 실행 구성을 적용한 저장소입니다.

## 시작

```bash
cd ~
git clone https://github.com/sonmap/Gcp_Managed_GKE_L2Comm03-01.git
cd ~/Gcp_Managed_GKE_L2Comm03-01
chmod +x gcloud/*.sh ssw/dlk/*.sh ssw/dlk/client_gke
chmod +x mnt/batch_gke/l2_gke_sh/rsvp/GP_L2RSVP_001_1/run-gke.sh
```

이미 내려받았다면 해당 디렉터리에서 `git pull --ff-only origin main`을 실행합니다.
단계별 실행·확인은 [RUNBOOK](docs/RUNBOOK.md)을 따릅니다.
기존 03에서 테스트한 인프라는 공유하므로 새 클러스터를 만들기 전에 현재 자원을 확인합니다.

## 구성

| 경로 | 역할 |
|---|---|
| `gcloud/` | API·IAM·네트워크·GKE·Cloud Build 구축 |
| `app/`, `cloudbuild/` | 이미지 소스와 빌드 정의 |
| `ssw/dlk/client_common` | RSVP NFS·마운트·키 경로 기본값 |
| `ssw/dlk/client_gke` | PV/PVC와 Pod 생성, 완료 대기 및 정리 |
| `ssw/dlk/run-gke.sh` | 공통 배치 실행 진입점 |
| `mnt/batch_gke/l2_gke_sh/rsvp/GP_L2RSVP_001_1/run-gke.sh` | RSVP 래퍼, VM 경로를 Pod 경로로 변환 |
| `mnt/batch_gke/l2/rsvp/GP_L2RSVP_001_1/python/bq_auth_smoke.py` | 키 인증으로 BigQuery SELECT 검사 |
| `mnt/python/` | 별도 조회 샘플. 기본 RSVP export에는 포함되지 않음 |
| `helm/`, `k8s/` | 참고용 매니페스트. RSVP 표준 실행 절차와 별도 |

## 실행 흐름

VM RSVP 래퍼 → 공통 run-gke.sh → client_gke → PV/PVC → GKE Autopilot Pod
→ NFS Python → BigQuery SELECT → 로그 출력 → 성공 Pod 삭제.
Workflows와 Cloud Scheduler는 이 실행 경로에서 사용하지 않습니다.

| 항목 | 현재 값 |
|---|---|
| 체크아웃 | `~/Gcp_Managed_GKE_L2Comm03-01` |
| Cloud Build 연결 저장소 | `Gcp_Managed_GKE_L2Comm03-01` |
| 전용 트리거 | `trg-l2comm03-01-python-image` |
| NFS 서버 export | `<repo>/mnt` → `/srv/l2comm-nfs` (NFSv4 루트) |
| Pod에서 사용하는 NFS 하위 경로 | `/batch_gke/l2/rsvp` |
| Pod 마운트 | `/home/jupyter` |
| 인증 파일 | VM `mnt/batch_gke/l2/rsvp/.oefj` → Pod `/home/jupyter/.oefj` |
| PV / PVC | `l2comm-rsvp-pv` / `l2comm-rsvp-pvc` |

키 파일은 VM에서 별도로 준비하며 Git에 반영하지 않습니다.
현재 클라이언트는 Pod 방식이며 Job TTL, KEEP_JOB, Cloud Logging 자동 폴백을 지원하지 않습니다.

설계는 [DESIGN](docs/DESIGN.md), 파일 역할은 [STRUCTURE](docs/STRUCTURE.md),
전환 시 주의사항은 [MIGRATION](docs/MIGRATION.md)을 참고하십시오.

BigQuery는 모든 Python 샘플에서 `.oefj` 키를 명시적으로 읽어 인증합니다.
`client_gke`는 KSA→GSA 어노테이션을 설정하지 않습니다.
Pod의 Kubernetes 실행에는 KSA가 계속 필요하지만 BigQuery 인증 계정은 키 파일의 서비스 계정입니다.
