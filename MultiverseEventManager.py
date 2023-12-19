from Network import Network
from Subscriber import Subscriber
from MVEvent import MVEvent
from MVEvent import MVProfile
import datetime
import time
import os

class MultiverseEventManager:
    SUBSCRIBER_PATH = './subscribers.csv'
    VERSION = 'v0.1.0'

    def __init__(self):
        print(f"Unseen Events {self.VERSION}")
        if not os.path.exists(self.SUBSCRIBER_PATH):
            print(f"Creating file {self.SUBSCRIBER_PATH}")
            print("Please add your account info to the list")
            with open(self.SUBSCRIBER_PATH, 'w') as f:
                f.write(
                    "platform,name,nutaku_id,user_id\nnutaku-steam-jp-tw,ExampleName,1234567,1010000001234")

        self.__reset()

    def __reset(self):
        print("Event Manager Setup...")
        self.Subscribers = []
        self.DefaultNetwork = Network('nutaku', 141433736, 1060000016502)
        self.Localization = self.getLocalization()
        self.mvEvent = self.getActiveEvent()
        self.__loadSubscribers()

    def __isActiveEvent(self):
        now = datetime.datetime.now().timestamp()
        if self.mvEvent == None:
            self.mvEvent = self.getActiveEvent()
        elif self.mvEvent.end < now:
            self.mvEvent = self.getActiveEvent()

        return self.mvEvent != None

    def __loadSubscribers(self):
        # print(f"Loading users from {self.SUBSCRIBER_PATH}")

        # get a list of users from the CSV file
        l = []
        with open(self.SUBSCRIBER_PATH, 'r') as f:
            for subscriber in f.readlines():
                if subscriber.startswith('platform,') or subscriber.startswith('nutaku-steam-jp-tw,'):
                    continue
                try:
                    data = subscriber.replace('\n', '').split(',')
                    uo = {'platform': data[0], 'name': data[1],
                          'nid': data[2], 'uid': data[3]}

                    l.append(uo)
                    # print(f"Parsed: {uo['name']} - {uo['nid']} - {uo['uid']}")

                except:
                    print(
                        "There is a problem with the subscriber csv file. user could not be parsed")

        # modifies adds new subscribers to the list
        for sub in l:
            found = False
            for user in self.Subscribers:
                if user.nid == sub['nid'] and user.uid == sub['uid']:
                    found = True
                    break

            if not found:
                try:
                    s = Subscriber(sub['platform'],
                                   sub['name'], sub['nid'], sub['uid'])
                    self.Subscribers.append(s)
                    print(
                        f"Add subscriber - name: {s.name}, username: {s.username}, nid: {s.nid}, uid: {s.uid}")
                except:
                    print(
                        "ERROR: problem while attempting to add subscriber. Please verify that the subscribers platform and ids are correct")

        # remove subscribers that were removed from the csv
        l2 = []
        for user in self.Subscribers:
            found = False
            for sub in l:
                if user.nid == sub['nid'] and user.uid == sub['uid']:
                    found = True
                    break

            if not found:
                print(
                    f"Remove subscriber - name: {user.name}, username: {user.username}, nid: {user.nid}, uid: {user.uid}")
            else:
                l2.append(user)
        self.Subscribers = l2

    def serverResetTime(self):
        t = datetime.datetime.now()
        t2 = datetime.datetime(t.year, t.month, t.day, 2, 0, 0)
        t2 += datetime.timedelta(days=1)
        return t2.timestamp()

    def getLocalization(self):
        print("Requesting localization data")
        csv = self.DefaultNetwork.gameFile("Localization.csv").text
        return csv.split('\n')

    """
        gets the active or upcomming sexual dating event
    """
    def getActiveEvent(self):
        print("Requesting Event Data")
        settings = self.DefaultNetwork.byteGameFile(
            "MultiverseEventSetting.zip", "MultiverseEventSetting.byte")

        future = None
        ongoing = None

        for event in settings['multiverse_dating_settings']:
            e = MVEvent(event, settings)

            now = datetime.datetime.now().timestamp()
            if now > e.start and now < e.end:
                ongoing = e
                break

            if now < e.end:
                future = e
                break

        if ongoing != None:
            return ongoing

        return future

    def getLevelSettings(self, level):
        for levelSettings in self.mvEvent.settings['multiverse_dating_level_settings']:
            if self.mvEvent.id == levelSettings['event_id'] and levelSettings['level'] == level:
                return levelSettings
            
    def getLevelCount(self):
        count = 0
        for chapter in self.mvEvent.settings['multiverse_dating_level_settings']:
            if self.mvEvent.id == chapter['event_id']:
               count +=1
        return count 
            
    def getMachineSettings(self, tier):
        current = None
        upgradeCost = None
        for m in self.mvEvent.settings['multiverse_dating_explore_item_settings']:
            if self.mvEvent.id != m['event_id']:
                continue
            if m['tier'] == tier:
                current = m
            if m['tier'] == tier+1:
                upgradeCost = m['tier_cost']

        current["upgrade_cost"] = upgradeCost

        return current
    
    def printEventAnswers(self):
        for level in self.mvEvent.settings['multiverse_dating_question_settings']:
            if self.mvEvent.id != level['event_id']:
                continue

            print(f"Level: {level['level']}")
            print("")

            for question in level['question']:
                print(f"Question: {question['content']}")
                choiceId = 0
                for answer in question['answer_list']:
                    choiceId += 1
                    if answer['is_true'] == 1:
                        print(f"Answer {choiceId}: {answer['answer']} ({answer['exp']} exp) ({answer['cost'][0]['amount']} energy)")
                print("")
            print("")
        
    """
        build the event profile for a user.
        the profile contains all information required to perform event operations
    """
    def buildProfile(self, sub: Subscriber):
        r = sub.network.event_mv_record()

        record = None
        for mvRecord in r['response']['user_multiverse_dating_records']:
            if mvRecord['event_id'] == self.mvEvent.id:
                record = mvRecord

        profile = MVProfile()
        profile.level = record['level']
        profile.exp = record['exp']
        profile.machineTier = record['item_tier']
        profile.question = record['current_question']
        
        profile.wine = 0
        profile.crystals = 0
        inv = sub.network.inventory()
        for item in inv['response']['user_item']:
            if item['item_id'] == self.mvEvent.wineId:
                profile.wine = item['amount']
            elif item['item_id'] == self.mvEvent.crystalId:
                profile.crystals = item['amount']

        return profile

    def run(self):
        while True:
            now = datetime.datetime.now().timestamp()

            # sleep till tomorrow if no event is found
            if not self.__isActiveEvent():
                tomorrow = self.serverResetTime()
                delta = tomorrow-now
                print(
                    f"No multiverse event found. Waiting till server reset to check again {delta/60/60} hours")
                time.sleep(delta)
                continue

            if not self.mvEvent.hasBeenSeen:
                print(
                    f"Event ID: {self.mvEvent.id}")
                self.mvEvent.hasBeenSeen = True
                self.printEventAnswers()

            if self.mvEvent.start > now:
                eventStart = self.mvEvent.start - now
                print(f"Multiverse event found. Waiting till event starts in {eventStart/60/60} hours")
                time.sleep(self.mvEvent.start - now)
                continue

            self.__loadSubscribers()

            if self.mvEvent.start <= now:
                for sub in self.Subscribers:
                    if sub.nextCollectTime < now:
                        sub.mvProfile = self.buildProfile(sub)
                        self.collect(sub)
                        self.setNextCollectTime(sub)

            # perform a check every 10 seconds
            time.sleep(10)

    def answerQuestions(self, sub: Subscriber):
        level = self.getLevelSettings(sub.mvProfile.level)

    def setNextCollectTime(self, sub:Subscriber):
        level = self.getLevelSettings(sub.mvProfile.level)
        levelMaxXP = level['exp']
        
        if (sub.mvProfile.level == self.getLevelCount() and 
            sub.mvProfile.exp == levelMaxXP):
            sub.nextCollectTime = self.serverResetTime()
            print(f"{sub.username} next collect time: {datetime.datetime.fromtimestamp(sub.nextCollectTime)}, Finished the current event waiting till tomorrow!")
            return

        machine = self.getMachineSettings(sub.mvProfile.machineTier)
        productionCapTime = machine['max_duration']
        productionInterval = machine['duration'] 

        # gets the time till next 
        standardTime = sub.lastClaimed + (productionCapTime - (productionInterval*2))

        sub.nextCollectTime = standardTime

        print(f"{sub.username} next collect time: {datetime.datetime.fromtimestamp(sub.nextCollectTime)} --- standard time was: {datetime.datetime.fromtimestamp(standardTime)}")


    """
        collects wine from the machine
    """
    def collect(self, sub: Subscriber):
        r = sub.network.event_mv_collect(self.mvEvent.id)
        sub.lastClaimed = r['server_time']

        if r['success'] == True:
            #update the wine supply
            sub.mvProfile.wine = r['updated_item_list'][0]['amount']
            print(f"{sub.username} has collected {r['response']['reward_list'][0]['amount']} wine")
        else:
            # set the wine supply
            print(f"{sub.username} ERROR_WINE_COLLECT: [{r['error_code']}]: {r['error_message']}")



e = MultiverseEventManager()
e.run()
