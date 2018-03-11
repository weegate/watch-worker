# -*- coding: utf-8-*-
# @by: wuyong
# @desc: update local gateway runtime server policy cache(lmdb) from remote config db(redis)
#   by zookeeper watch the meta node
# @date: 2017-12-17
# @todo: review code

import os,time
import signal
import requests
import json
from kazoo.client import KazooClient,KazooState,KeeperState
import lmdb
import redis
import yaml
import lib.util
from policy.bootstrap import Bootstrap

interrupted = False

dict_runtime_policy_keys = {
    "userInfoModulename": "ab:runtimeInfo:>>SERVER_NAME<<:>>STEP<<:userInfoModulename",
    "divDataKey": "ab:runtimeInfo:>>SERVER_NAME<<:>>STEP<<:divDataKey",
    "divModulename": "ab:runtimeInfo:>>SERVER_NAME<<:>>STEP<<:divModulename",
}

dict_runtime_policy_steps_keys = {
    "divsteps": "ab:runtimeInfo:>>SERVER_NAME<<:divsteps",
}

dict_policy_type_keys ={
    "divtype": "ab:policies:>>ID<<:divtype",
}

dict_policy_data_keys ={
    "divdata": "ab:policies:>>ID<<:divdata",
}

dict_policy_group_keys ={
    "policyGroupsID": "ab:policygroups:>>ID<<",
}

dict_priority_keys = {
    "1": "first",
    "2": "second",
    "3": "third",
    "4": "fourth",
    "5": "fifth",
    "6": "sixth",
    "7": "seventh",
    "8": "eight",
    "9": "ninth",
}
max_policy_num=10

def signal_handler(signal, frame):
    logger.info("signal:%s,frame:%s",signal,frame)
    global interrupted
    interrupted = True

def interrupt_callback():
    global interrupted
    return interrupted

# capture SIGINT signal, e.g., Ctrl+C
#signal.signal(signal.SIGINT, signal_handler)
#signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGUSR1, signal_handler)
signal.signal(signal.SIGUSR2, signal_handler)

logger = lib.util.init_logger("watch_worker")

conf_file = lib.util.config("worker.yaml")
if os.path.exists(conf_file) is False:
    logger.info("%s is not exists! please check it."%(conf_file,))

try:
    with open(conf_file, "r") as f:
        config = yaml.safe_load(f)
except OSError:
    logger.error("Can't open config file: '%s'", conf_file)
    raise

env = os.getenv("NODE_ENV") if os.getenv("NODE_ENV") else "default"
logger.info("env: '%s'", env)
zk_hosts = config['zk'][env]['hosts'] if config['zk'][env]['hosts'] else ""

redis_host = config['redis'][env]['host'] if config['redis'][env]['host'] else ""
redis_port = config['redis'][env]['port'] if config['redis'][env]['port'] else 6379
redis_password = config['redis'][env]['password'] if config['redis'][env]['password'] else ""
redis_db = config['redis'][env]['db'] if config['redis'][env]['db'] else 0

lmdb_path = config['lmdb'][env]['db_path'] if config['lmdb'][env]['db_path'] else lib.util.data("runtime_policy")
db_name = config['lmdb'][env]['db_name'] if config['lmdb'][env]['db_name'] else None
max_dbs = config['lmdb'][env]['max_dbs'] if config['lmdb'][env]['max_dbs'] else 1
logger.info("lmdb_path:%s\tdb_name:%s\tmax_dbs:%s\t"%(lmdb_path,db_name,max_dbs))

shared_dict_update_uri = config['shared_dict'][env]['update_uri_path'] if config['shared_dict'][env]['update_uri_path'] else "http://10.5.27.238:9191/update"
logger.info("shared dict update uri path:%s"%(shared_dict_update_uri))

def watch_for_ro(state):
    if state == KazooState.LOST:
        logger.info("zk connect lost!")
        pass
    elif state == KazooState.SUSPENDED:
        logger.info("zk connect suspended!")
        pass
    elif state == KazooState.CONNECTED:
        if zk.client_state == KeeperState.CONNECTED_RO:
            logger.info("Read only mode!")
        else:
            logger.info("Read/Write mode!")
    else:
        logger.info("zk other state!")
        pass

zk = KazooClient(hosts=zk_hosts,read_only=True)
zk.start()
zk.add_listener(watch_for_ro)

def readCheckLmdb(lmdb_path,db_name,max_dbs,runtime_policy_meta):
    if runtime_policy_meta is not None:
        env = lmdb.Environment(path=lmdb_path,max_dbs=max_dbs)
        db_handle = env.open_db(db_name)
        txn = env.begin(write=False,db=db_handle)

        rs = redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db, password=redis_password)

        # runtimeInfo
        key = dict_runtime_policy_steps_keys['divsteps'].replace(">>SERVER_NAME<<",runtime_policy_meta['server_name'])
        div_steps = rs.get(key)
        val = txn.get(key=key.encode())
        logger.info("key-value:\t%s\t%s"%(key,val))

        for k,r_key in dict_runtime_policy_keys.iteritems():
            re_key = r_key.replace(">>SERVER_NAME<<",runtime_policy_meta['server_name'])

            if 'policy_id' in runtime_policy_meta:
                logger.info("policy_id:%s"%(runtime_policy_meta['policy_id'],))
                key = re_key.replace(">>STEP<<","first")
                val = txn.get(key=key.encode())
                logger.info("key-value:\t%s\t%s"%(key,val))

            if 'policy_group_id' in runtime_policy_meta:
                for step in range(1,int(div_steps)+1,1):
                    key = re_key.replace(">>STEP<<",dict_priority_keys[str(step)])
                    val = txn.get(key=key.encode())
                    logger.info("key-value:\t%s\t%s"%(key,val))

        # runtime use request_body
        if 'policy_id' in runtime_policy_meta:
            policy_id = str(runtime_policy_meta['policy_id'])
            logger.info("policy_id:%s"%(policy_id))

            # divtype
            key = dict_policy_type_keys['divtype'].replace(">>ID<<",policy_id)
            val = txn.get(key=key.encode())
            logger.info("key-value:\t%s\t%s"%(key,val))

            # divdata
            key = dict_policy_data_keys['divdata'].replace(">>ID<<",policy_id)
            val = txn.get(key=key.encode())
            logger.info("key-value:\t%s\t%s"%(key,val))

        if 'policy_group_id' in runtime_policy_meta:
            policy_group_id = str(runtime_policy_meta['policy_group_id'])
            logger.info("policy_group_id:%s"%(policy_group_id))

            key = dict_policy_group_keys['policyGroupsID'].replace(">>ID<<",policy_group_id)
            policy_ids = rs.lrange(key,0,max_policy_num)
            for policy_id in policy_ids:
                policy_id = str(policy_id)
                logger.info("policy_id:%s"%(policy_id,))

                # divtype
                key = dict_policy_type_keys['divtype'].replace(">>ID<<",policy_id)
                val = txn.get(key=key.encode())
                logger.info("key-value:\t%s\t%s"%(key,val))

                # divdata
                key = dict_policy_data_keys['divdata'].replace(">>ID<<",policy_id)
                val = txn.get(key=key.encode())
                logger.info("key-value:\t%s\t%s"%(key,val))


        env.close()

def write2LocalLmdbFromRedis(lmdb_path,db_name,max_dbs, runtime_policy_meta):
    # notice: 32bit os map max size 2G
    env = lmdb.Environment(path=lmdb_path,map_size=int(1<<31),max_dbs=max_dbs)
    db_handle = env.open_db(db_name)
    txn = env.begin(write=True,buffers=True,db=db_handle)

    rs = redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db, password=redis_password)

    # runtimeInfo
    key = dict_runtime_policy_steps_keys['divsteps'].replace(">>SERVER_NAME<<",runtime_policy_meta['server_name'])
    logger.info("key:\t%s"%(key,))
    div_steps = rs.get(key)
    logger.info("div_steps:\t%s"%(div_steps.encode(),))
    txn.replace(key.encode(),div_steps.encode())

    for k,r_key in dict_runtime_policy_keys.iteritems():
        re_key = r_key.replace(">>SERVER_NAME<<",runtime_policy_meta['server_name'])

        if 'policy_id' in runtime_policy_meta:
            logger.info("policy_id:%s"%(runtime_policy_meta['policy_id'],))
            key = re_key.replace(">>STEP<<","first")
            logger.info("key:\t%s"%(key,))
            val = rs.get(key)
            logger.info("val:\t%s"%(val,))
            txn.replace(key.encode(),val.encode())

        if 'policy_group_id' in runtime_policy_meta:
            for step in range(1,int(div_steps)+1,1):
                key = re_key.replace(">>STEP<<",dict_priority_keys[str(step)])
                logger.info("key:\t%s"%(key,))
                val = rs.get(key)
                logger.info("val:\t%s"%(val,))
                txn.replace(key.encode(),val.encode())

    # the used request_body of runtime
    if 'policy_id' in runtime_policy_meta:
        policy_id = str(runtime_policy_meta['policy_id'])
        logger.info("policy_id:%s"%(policy_id))

        # divtype
        key = dict_policy_type_keys['divtype'].replace(">>ID<<",policy_id)
        val = rs.get(key)
        logger.info("val:\t%s"%(val,))
        txn.replace(key.encode(),val.encode())

        # divdata
        key = dict_policy_data_keys['divdata'].replace(">>ID<<",policy_id)
        logger.info("key:\t%s"%(key,))
        divedata_key_type = rs.type(key)
        logger.info("divedata_key_type:\t%s"%(divedata_key_type,))

        if "string" == divedata_key_type:
            val = rs.get(key)
            logger.info("val:\t%s"%(val,))
            txn.replace(key.encode(),val.encode())
        elif "hash" == divedata_key_type:
            val = rs.hgetall(key)
            logger.info("val:\t%s"%(json.dumps(val),))
            txn.replace(key.encode(),json.dumps(val).encode())
        elif "set" == divedata_key_type:
            val = rs.smembers(key)
            logger.info("val:\t%s"%(json.dumps(val),))
            txn.replace(key.encode(),json.dumps(val).encode())
        elif "list" == divedata_key_type:
            val = rs.lrange(key,start=0,end=-1)
            logger.info("val:\t%s"%(json.dumps(val),))
            txn.replace(key.encode(),json.dumps(val).encode())
        elif "zset" == divedata_key_type:
            val = rs.zrange(key,start=0,end=-1,withscores=True)
            logger.info("val:\t%s"%(json.dumps(val),))
            txn.replace(key.encode(),json.dumps(val).encode())

        policyObj.getUpStreamsToLocalCache(val,txn,logger)


    if 'policy_group_id' in runtime_policy_meta:
        policy_group_id = str(runtime_policy_meta['policy_group_id'])
        logger.info("policy_group_id:%s"%(policy_group_id))

        key = dict_policy_group_keys['policyGroupsID'].replace(">>ID<<",policy_group_id)
        policy_ids = rs.lrange(key,0,max_policy_num)
        for policy_id in policy_ids:
            policy_id = str(policy_id)
            logger.info("policy_id:%s"%(policy_id,))

            # divtype
            key = dict_policy_type_keys['divtype'].replace(">>ID<<",policy_id)
            logger.info("key:\t%s"%(key,))
            val = rs.get(key)
            logger.info("val:\t%s"%(val,))
            txn.replace(key.encode(),val.encode())

            # divdata
            key = dict_policy_data_keys['divdata'].replace(">>ID<<",policy_id)
            logger.info("key:\t%s"%(key,))
            divedata_key_type = rs.type(key)
            logger.info("divedata_key_type:\t%s"%(divedata_key_type,))

            if "string" == divedata_key_type:
                val = rs.get(key)
                logger.info("val:\t%s"%(val,))
                txn.replace(key.encode(),val.encode())
            elif "hash" == divedata_key_type:
                val = rs.hgetall(key)
                logger.info("val:\t%s"%(json.dumps(val),))
                txn.replace(key.encode(),json.dumps(val).encode())
            elif "set" == divedata_key_type:
                val = rs.smembers(key)
                logger.info("val:\t%s"%(json.dumps(val),))
                txn.replace(key.encode(),json.dumps(val).encode())
            elif "list" == divedata_key_type:
                val = rs.lrange(key,start=0,end=-1)
                logger.info("val:\t%s"%(json.dumps(val),))
                txn.replace(key.encode(),json.dumps(val).encode())
            elif "zset" == divedata_key_type:
                val = rs.zrange(key,start=0,end=-1,withscores=True)
                logger.info("val:\t%s"%(json.dumps(val),))
                txn.replace(key.encode(),json.dumps(val).encode())

            policyObj.getUpStreamsToLocalCache(val,txn,logger)

    txn.commit()
    env.close()

def updateLocalCacheFromLmdb(uri,runtime_policy_meta):
    querystring = {"host":runtime_policy_meta['server_name']}

    response = requests.request("GET", uri, params=querystring)
    if response.status_code != 200:
        logger.error("server_name: %s update failed~!, request %s is failed~!" % (runtime_policy_meta['server_name'],uri))
        return
    resp = json.loads(response.content)
    logger.info("response: %s" % (resp,))
    code = resp['code']
    if code == 200:
        logger.info("server_name: %s update runtime policy to shared dict success!" % (runtime_policy_meta['server_name'],))
    else:
        msg = resp['desc'].encode("utf-8")
        logger.info("server_name: %s update failed~！ error msg: %s" % (runtime_policy_meta['server_name'],msg))

bootstrapObj = Bootstrap()
policies = bootstrapObj.get_policies()
for policyObj in policies:
    policy_node_path = bootstrapObj.get_policy_node_path(policyObj.CATE,policyObj.TAG)

    if zk.exists(policy_node_path) is None:
        zk.ensure_path(policy_node_path)

    @zk.DataWatch(policy_node_path)
    def watch_node(data, stat):
        logger.info("Version: %s, data: %s" % (stat.version, data.decode("utf-8")))
        if data == "":
            logger.error("get %s is empty",policy_node_path)
            return None
        runtime_policy_meta = json.loads(data)
        if runtime_policy_meta is None:
            logger.error("runtime_policy_meta %s is None",runtime_policy_meta)
            return None

        write2LocalLmdbFromRedis(lmdb_path, db_name, max_dbs, runtime_policy_meta)

        updateLocalCacheFromLmdb(shared_dict_update_uri,runtime_policy_meta)

        #readCheckLmdb(lmdb_path, db_name, max_dbs, runtime_policy_meta)



while True:
    if interrupt_callback():
        zk.stop()
        break
    time.sleep(100)

