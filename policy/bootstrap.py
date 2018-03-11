# -*- coding: utf-8-*-
import os
import lib
import pkgutil

class Bootstrap(object):

    def __init__(self):
        self.policy_config = lib.util.get_policy_config()

    def get_policies(self):
        """
        通过引导配置获取策略插件模块，通过插件模块中的PRIORITY属性控制优先级，按大到小排序，越大越优先
        """
        policys = []
        locations = []
        tags = []
        cates = []
        logger = lib.util.init_logger(__name__)
        for (cate,policy_tags) in self.policy_config.items():
            locations.append(os.path.join(lib.util.POLICY_PATH,cate))
            tags.extend(policy_tags.keys())
            cates.append(cate)

        tags = list(set(tags))

        for finder, name, ispkg in pkgutil.walk_packages(locations):
            try:
                loader = finder.find_module(name)
                policy = loader.load_module(name)
            except:
                logger.warning("Skipped policy '%s' due to an error.", name, exc_info=True)
            else:
                if ( (hasattr(policy, 'isValid'))
                     and (hasattr(policy, 'getUpStreamsToLocalCache'))
                     and (hasattr(policy, 'TAG')) and (policy.TAG in tags)
                     and (hasattr(policy, 'CATE')) and (policy.CATE in cates) ):
                    logger.debug("Found policy '%s' with tag: %r", name, policy.TAG)
                    policys.append(policy)
                else:
                    logger.warning("Skipped policy '%s' maybe it misses " + "the TAG/CATE constant.", name)

        policys.sort(key=lambda mod: mod.PRIORITY if hasattr(mod, 'PRIORITY') else 0, reverse=True)

        return policys

    def get_policy_node_path(self,cate,tag):
        """
        get policy node path by policy category and policy tag
        :param cate: policy category （CATE) eg: request_body,uri,head
        :param tag: policy tag (TAG) eg: countryCode
        :return:
        """
        return self.policy_config[cate][tag]['watch_zk_node_path'] if (cate in self.policy_config and tag in self.policy_config[cate]) else None
