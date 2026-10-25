# L2Comm03 → L2Comm03-01 전환

03-01은 03의 gcloud 인프라 코드에 02의 `feature/rsvp-pod-oefj-mount`
브랜치(commit `61710d221042e202eb24744e2cbd3998d62aedcd`)의 `ssw/`, `mnt/`를 적용했습니다.

| 항목 | 03 | 03-01 |
|---|---|---|
| 체크아웃 | `~/Gcp_Managed_GKE_L2Comm03` | `~/Gcp_Managed_GKE_L2Comm03-01` |
| Cloud Build 저장소 | `Gcp_Managed_GKE_L2Comm03` | `Gcp_Managed_GKE_L2Comm03-01` |
| 트리거 | `trg-l2comm03-python-image` | `trg-l2comm03-01-python-image` |
| 실행 리소스 | Job | Pod |
| NFS 하위 경로 | `/` | `/batch_gke/l2/rsvp` |
| Pod 마운트 | `/mnt/l2comm` | `/home/jupyter` |
| 기본 검사 | 이미지 내부 적재 / NFS 조회 | RSVP 키 인증 SELECT |
| 성공 후 정리 | Job 삭제 | Pod 삭제 |
| 인프라 | 기존 Shared VPC·GKE·AR | 같은 인프라 재사용 |

기존 구축을 삭제할 필요가 없습니다. RUNBOOK §4-3에서 새 체크아웃을 준비한 뒤
기존 플랫폼을 조회하고 §10에서 `/ssw/dlk` 링크와 NFS bind mount를 새 경로로 전환합니다.
전환은 실행 중인 배치가 없는 시간에 수행합니다. 키는 Git에 올리지 않고 VM에서 준비합니다.

새 저장소의 자동 빌드가 필요하면 GitHub App 접근 목록에 03-01을 추가하고
`20-source-connection.sh`, `30-platform.sh`의 해당 연결·트리거 구성을 확인합니다.
03 트리거는 별도이며 자동으로 삭제하지 않습니다. 두 트리거는 동일 이미지 태그를 갱신할 수 있습니다.

`90-teardown.sh`는 공유 자원을 삭제하므로 단순 재테스트용으로 실행하지 않습니다.
`KEEP_JOB`, `debug-gke.sh`, `REPOINT=true`는 현재 실행 코드에서 지원하지 않습니다.
