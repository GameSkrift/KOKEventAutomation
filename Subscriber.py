from Network import Network
from SDEvent import SDProfile
from MVEvent import MVProfile

class Subscriber:

    def __init__(self, platform, name, nid, uid):
        self.network = Network(platform, nid, uid)
        info = self.network.user()

        self.name = name
        self.uid = info['user_id']
        self.aid = info['acc_id']
        self.nid = nid
        self.username = info['display_name']
        self.created = info['create_account_time']
        self.lastOnline = info['last_login_time']

        self.lastClaimed = 0
        self.nextCollectTime = 0

        self.sdProfile = SDProfile()
        self.mvProfile = MVProfile()
