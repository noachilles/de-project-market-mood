# 은주
## MM-19: feedDataStore  
### Back-end  
Docker 환경에 postgres를 올리고, 실행하므로 settings의 DB HOST 설정은 'postgres'임  
* migrate 주의사항   
  위의 내용으로 인해서, local에서 python을 실행하면 안 되고, docker 환경에 접속한 다음 migrate 진행해야 함  
  한편, runserver는 실행할 필요가 없음(`Docker compose up`과 동시에 올라감)  

#### 특정 Docker에 진입하는 방법  
```bash
docker exec -it {container_id} bash
```

### Data-end  
