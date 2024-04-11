# [HitCircle API](https://github.com/Tsurumaki-Kokoro/HitCircle-API) &middot; [![Licence](https://img.shields.io/github/license/Ileriayo/markdown-badges?style=for-the-badge)](https://github.com/Tsurumaki-Kokoro/HitCircle-API/blob/master/LICENCE) ![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54) ![GitHub Actions](https://img.shields.io/badge/github%20actions-%232671E5.svg?style=for-the-badge&logo=githubactions&logoColor=white)

HitCircle API 是一个基于 FastAPI 的 机器人后端 API 项目，用于提供 osu! 相关的数据查询服务, 并以图片、文字等形式返回。

## 项目介绍
本项目基于 FastAPI 框架，易于跨平台移植部署。解决机器人更换到新平台需要大量重写代码的问题。支持查询图片多主题自由切换，可自定义主题样式。

部分功能的默认主题基于 [nonebot-plugin-osubot](https://github.com/yaowan233/nonebot-plugin-osubot)、[osuv2](https://github.com/Yuri-YuzuChaN/osuv2) 修改而来。

## 已实现主要功能
- [x] 跨平台绑定 osu! 用户
- [x] 查询 osu! 用户信息
- [x] 查询 osu! 用户最近游玩记录（包含 Failed）
- [x] 查询 osu! 用户BP记录、单图成绩
- [x] 查询 osu! Beatmap、Beatmapset 信息

## 即将实现功能
- [ ] 群组 osu! 用户排行榜
- [ ] 查询并重新计算 osu! 用户成绩(无 Choke)
- [ ] 查询比对其他用户的 osu! 数据、成绩
- [ ] 查询 osu! Multiplayer 比赛总结
- [ ] 查询 osu! 实时跟踪 Multiplayer 比赛信息

## 项目部署
<details>
<summary>Docker Compose 部署 </summary>

>新建文件夹，将以下内容保存为 `docker-compose.yml` 文件, 并将 `.env` 文件放置在同一目录下。

**docker-compose.yml**
```yaml
services:
api_backend:
    image: tr4nce/hit-circle-api:latest
    volumes:
      - log_volume:/app/logs
    env_file:
      - .env
    ports:
      - "8900:8900"

redis:
    image: redis:latest
    ports:
      - "6379:6379"

volumes:
log_volume:
```

**.env**
```env
API_KEY=your_api_key
OSU_CLIENT_ID=your_osu_client_id
OSU_CLIENT_SECRET=your_osu_client_secret
DB_HOST=mysql
DB_PORT=3306
DB_USER=root
DB_PASSWORD=root
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
```

**Redis 相关配置不需要修改，其他配置请根据实际情况修改。**

>运行以下命令启动服务
```bash
docker-compose pull
docker-compose up -d
```
</details>

<details>
<summary>手动部署 </summary>

1. 安装 Python 3.11+
2. 安装 MySQL & Redis
3. 安装依赖
    ```bash
    pip install -r requirements.txt
    ```
4. 修改 `./app/config.py` 文件中的数据库配置, 并将 Debug 改为 True
    ```python
    DEBUG = True
    
    if DEBUG:
        API_KEY = "123456asdfgh"
        CLIENT_ID = 114514
        CLIENT_SECRET = "secret"
        DB_HOST = "localhost"
        DB_PORT = 3306
        DB_USER = "root"
        DB_PASSWORD = "password"
        REDIS_HOST = "localhost"
        REDIS_PORT = 6379
        REDIS_DB = 1
    ```
5. 运行项目
    ```bash
    uvicorn main:app --reload --host 0.0.0.0 --port 8900
    ```

</details>

