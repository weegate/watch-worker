'''
@todo: key must only one, so add unique prefix
'''

TAG = 'countryCode'
CATE = "request_body"
PRIORITY = 1

country_codes = ["AD","AE","AF","AG","AI","AL","AM","AO","AR","AS","AT","AU","AW","AZ","BA","BB","BD","BE","BF","BG","BH","BI","BJ","BL","BM","BN","BO","BR","BS","BT","BW","BY","BZ","CA","CD","CF","CG","CH","CK","CL","CM","CN","CO","CR","CU","CV","CW","CY","CZ","DE","DJ","DK","DM","DO","DZ","EC","EE","EG","ES","ET","FI","FJ","FK","FO","FR","GA","GB","GD","GE","GF","GG","GH","GI","GL","GM","GN","GP","GQ","GR","GT","GW","GY","HK","HN","HR","HT","HU","ID","IE","IL","IM","IN","IO","IQ","IR","IS","IT","JE","JM","JO","JP","KE","KG","KH","KM","KR","KW","KY","KZ","LA","LB","LC","LI","LK","LR","LS","LT","LU","LV","LY","MA","MC","MD","ME","MG","MH","MK","ML","MM","MN","MO","MQ","MR","MS","MT","MU","MV","MW","MX","MY","MZ","NA","NC","NE","NF","NG","NI","NL","NO","NP","NR","NZ","OM","PA","PE","PF","PG","PH","PK","PL","PM","PS","PT","PW","PY","QA","RE","RO","RS","RU","RW","SA","SB","SC","SD","SE","SG","SI","SK","SL","SM","SN","SO","SR","SS","ST","SV","SX","SY","SZ","TC","TD","TG","TH","TJ","TL","TM","TN","TO","TR","TT","TW","TZ","UA","UG","US","UY","UZ","VC","VE","VN","VU","WF","WS","YE","ZA","ZM","ZW"]

def isValid():

    return True

def getUpStreamsToLocalCache(schema,txn,logger):
    """
    get upstream set to lmdb from remote db diversion data schema
    :param schema: list - remote db diversion data schema
    :param txn: lmdb transaction obj - local cache db
    :param logger: print trace log
    :return:
    """
    assert(type(schema) is dict)
    for countryCode in country_codes:
        key = countryCode
        if countryCode in schema:
            val = schema[countryCode]
        else:
            val = schema['OTHER'] if 'OTHER' in schema else "ofo_global_base_api"

        txn.put(key.encode(),val.encode())
        logger.info("countryCode ==> key:%s\tval:%s"%(key,val))


