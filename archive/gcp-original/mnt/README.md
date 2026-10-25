# 03-01 NFS 소스

VM export 루트는 `~/Gcp_Managed_GKE_L2Comm03-01/mnt`입니다.
RSVP 클라이언트는 그 아래 `/batch_gke/l2/rsvp`를 `/home/jupyter`에 마운트합니다.

| 경로 | 용도 |
|---|---|
| `batch_gke/l2/rsvp/GP_L2RSVP_001_1/python/bq_auth_smoke.py` | Pod에서 실행하는 인증 검사 |
| `batch_gke/l2_gke_sh/rsvp/GP_L2RSVP_001_1/run-gke.sh` | VM에서 실행하는 RSVP 래퍼 |
| `python/bq_sample.py` | 별도 조회 샘플. 기본 RSVP export에는 포함되지 않음 |

`.oefj`는 `batch_gke/l2/rsvp/`에 VM에서 별도로 준비하며 Git에 올리지 않습니다.
실행은 [RUNBOOK](../docs/RUNBOOK.md) §10~11을 따릅니다.
