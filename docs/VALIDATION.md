# 검증 결과

검증 기준일: 2026-10-25. Azure 구독에 로그인하거나 자원을 생성하지 않았다.

| 검증 | 결과 |
|---|---|
| 활성 Bash 스크립트 문법 | 통과 |
| RUNBOOK의 Bash 명령 블록 16개 문법 | 통과 |
| app 및 mnt Python 컴파일 | 통과 |
| 기존 업무 wrapper DRY_RUN | 통과: ACR 이미지·NFS·.oefj·Pod 내부 경로 |
| DOCKER_IMAGE 누락 | 실행 거부 확인 |
| Pod Succeeded 모의 실행 | 로그 출력 후 Pod 삭제 확인 |
| Pod Failed 모의 실행 | 즉시 실패 처리·Pod 보존·describe 확인 |
| 원본 보존 | 원본 35개 파일을 archive/gcp-original에 저장 |

재현:
```bash
python3 -m unittest discover -s tests -v
```

테스트는 mock kubectl을 사용하며 실제 AKS·NFS·BQ에 접근하지 않는다.
실배포 전 필수 확인: CIDR 중복, SKU/quota, Azure CLI 버전, Entra 역할·정책,
ACR Tasks, NAT·Private DNS, NFS 접근·UID/GID, GCP BigQuery egress·권한.
원본 Git 컨텍스트가 있어야 업무 wrapper의 git rev-parse가 동작한다. 테스트도 clone된 저장소에서 실행한다.
