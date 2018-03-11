### intro
网关旁路worker脚本，比如：
- [x] 更新本地策略缓存 
- [ ] 用于实现旁路监控zk的服务注册节点，网关ngx-lua动态从本地缓存中更新upstream(...打补丁的方式...)

### script-worker
> `export PYTHON_ENV=default/dev/qa/product && mkdir -p {logs,pid}` before run those script
* watch_to_update_local_cache_worker.py: 监控运行时策略配置，实时获取远端运行时策略配置，更新本地缓存（全量替换更新）

### data
> `sudo mkdir -p /data/lmdb && sudo chown -R www:www /data/lmdb` before run those script by *ops* user

> use mdb_dump,mdb_load lmdb自带的工具进行导出导入


### config
* `worker.yaml`: 配置worker脚本中依赖的服务配置和基本配置，zk,redis,lmdb,log
* `policy.yaml`: 根据分类(CATE)和标签(TAG)配置策略节点，每配置一个策略，需要在policy文件夹对应分类文件夹中添加策略处理逻辑，主要是将远程db中的配置写入本地缓存中，在该新加处理策略逻辑文件中加入对应的CATE和TAG,以及优先级PRIORITY


### howto
> 1.定义配置： policy.yaml 中定义的是zk节点路径，存放某个运行时策略元信息;如果新加策略，配置上对应线上开发好的网关策略节点路劲就可以了;
> 2.运行：直接npm run pm2_dev/pm2_qa/pm2/default


### Notice
> watch_to_update_local_cache_worker.py脚本中相关`policy_group_id` 已废弃，占时不用 



