# 03-01 VM 실행 스크립트

작업 디렉터리: `~/Gcp_Managed_GKE_L2Comm03-01`.

| 파일 | 역할 |
|---|---|
| `install-vm.sh` | `/ssw/dlk` 최초 심볼릭 링크 생성. 기존 다른 링크는 자동 교체하지 않음 |
| `setup-nfs-server.sh` | 현재 체크아웃의 `mnt/`를 `/srv/l2comm-nfs`로 bind/export |
| `client_common` | NFS RSVP 경로, `/home/jupyter`, `.oefj`, PV/PVC 기본값 |
| `run-gke.sh` | 날짜·리소스·작업 경로·프로그램 인자 전달 |
| `client_gke` | PV/PVC·Pod 생성 및 대기·로그·성공 정리 |

```bash
cd ~/Gcp_Managed_GKE_L2Comm03-01
chmod +x ssw/dlk/*.sh ssw/dlk/client_gke
chmod +x mnt/batch_gke/l2_gke_sh/rsvp/GP_L2RSVP_001_1/run-gke.sh
```

기존 링크 재연결, NFS 전환, 키 확인, DRY_RUN 및 실제 실행은
[RUNBOOK](../../docs/RUNBOOK.md) §10~11을 따릅니다.
공통 run-gke.sh를 직접 호출할 때는 Pod 작업 경로를 지정합니다.
RSVP 래퍼는 기존 `/mnt/batch_gke/l2/rsvp/...` 인자를 `/home/jupyter/...`로 변환합니다.
Job·KEEP_JOB·debug-gke.sh·Cloud Logging 자동 폴백은 지원하지 않습니다.
