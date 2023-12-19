from Network import Network
from Subscriber import Subscriber
from SDEvent import SDEvent
from SDEvent import SDProfile
import datetime
import re
import time
import os
import math


class EventManager:

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
        self.sdEvent = self.getActiveEvent()
        self.__loadSubscribers()

    def __isActiveEvent(self):
        now = datetime.datetime.now().timestamp()
        if self.sdEvent == None:
            self.sdEvent = self.getActiveEvent()
        elif self.sdEvent.end < now:
            self.sdEvent = self.getActiveEvent()

        return self.sdEvent != None

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
            "SexualDatingSetting.zip", "SexualDatingSetting.byte")

        future = None
        ongoing = None

        for event in settings['sexual_dating_settings']:
            e = SDEvent(event, settings)

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

    def getAssetIdByName(self, name):
        l = []
        for line in self.Localization:
            cells = line.split(',')
            if len(cells) <= 1:
                continue

            if name in cells[1]:
                id = re.findall(r'(?=.*_?)\d+(?=_?.*)', cells[0])[0]
                l.append(id)
                print(f"found value: {line} -- id: {id}")

        return l

    def getAssetNameById(self, assetId):
        for line in self.Localization:
            cells = line.split(',')
            if len(cells) <= 1:
                continue

            id = cells[0]

            if (id == f"pet_name_{assetId}" or
                id == f"item_name_{assetId}" or
                id == f"Equipment_{assetId}_name" or
                id == f"Artifact_Name_{assetId}" or
                    id == f"Flag_Name_{assetId}"):
                return cells[1]

            return "NaN"
    
    def getStoryMessageSavePoints(self, chapterId):
        messages = []
        for chapter in self.sdEvent.settings['message_detail_settings']:
            if self.sdEvent.id != chapter['event_id'] or chapter['chapter'] != chapterId:
                continue

            for message in chapter['message_data']:
                if message['save_point'] == 1:
                    messages.append(message)
        
        return messages

    def getSceneSettings(self,chapterId):
        for chapter in self.sdEvent.settings['h_sence_settings']:
            if self.sdEvent.id == chapter['event_id']:
                if chapter['chapter_id'] == chapterId:
                    return chapter
            
    def getChapterCount(self):
        count = 0
        for chapter in self.sdEvent.settings['h_sence_settings']:
            if self.sdEvent.id == chapter['event_id']:
               count +=1
        return count 
            
    def getMachineSettings(self, tier):
        current = None
        upgradeCost = None
        for m in self.sdEvent.settings['explore_item_settings']:
            if self.sdEvent.id != m['event_id']:
                continue
            if m['tier'] == tier:
                current = m
            if m['tier'] == tier+1:
                upgradeCost = m['cost_list']

        current["upgrade_cost"] = upgradeCost

        return current
    
    def getClickOption(self, chapterId, optionIndex):
        chapter = self.getSceneSettings(chapterId)
        options = chapter['option_detail']
        option = options[optionIndex]

        if optionIndex < len(options)-1:
            option['nextOptionAtExp'] = options[optionIndex+1]['exp_require']

        return option
    
    def printEventAnsers(self):
        for chapter in self.sdEvent.settings['message_detail_settings']:
            if self.sdEvent.id != chapter['event_id']:
                continue
            print(f"Chapter {chapter['name']}")
            for message in chapter['message_data']:
                choiceId = 0
                for selection in message['selection_list']:
                    choiceId += 1
                    if selection['correct'] == 1:
                        print(f"\tAnswer {choiceId}: {selection['content']} ({selection['item_cost'][0]['amount']} wine)")
                        break
        
    """
        build the event profile for a user.
        the profile contains all information required to perform event operations
    """
    def buildProfile(self, sub: Subscriber):
        r = sub.network.event_sd_record(self.sdEvent.id)

        profile = SDProfile()
        profile.chapter = r['response']['user_record']['current_chapter']
        profile.exp = r['response']['user_record']['exp']
        profile.option = r['response']['user_record']['unlock_option'][-1]
        profile.machineTier = r['response']['user_explore_item_record']['tier']
        profile.savePoint = r['response']['user_record']['last_message_id']
        
        if len(r['response']['user_record']['selection']) > 0:
            profile.lastSelection = int(r['response']['user_record']['selection'][-1].split('_')[0])
        
        profile.wine = 0
        profile.hurbs = 0
        inv = sub.network.inventory()
        for item in inv['response']['user_item']:
            if item['item_id'] == self.sdEvent.wineId:
                profile.wine = item['amount']
            elif item['item_id'] == self.sdEvent.herbsId:
                profile.hurbs = item['amount']

        return profile

    def run(self):
        while True:
            now = datetime.datetime.now().timestamp()

            # sleep till tomorrow if no event is found
            if not self.__isActiveEvent():
                tomorrow = self.serverResetTime()
                delta = tomorrow-now
                print(
                    f"No sexual dating event found. Waiting till server reset to check again {delta/60/60} hours")
                time.sleep(delta)
                continue

            if not self.sdEvent.hasBeenSeen:
                print(
                    f"Event Name: {self.sdEvent.name}, ID: {self.sdEvent.id}")
                self.sdEvent.hasBeenSeen = True
                self.printEventAnsers()

            # precollect wine till event starts
            if self.sdEvent.start > now:
                for sub in self.Subscribers:
                    if sub.nextCollectTime < now:
                        sub.sdProfile = self.buildProfile(sub)
                        self.collect(sub)
                        self.setNextCollectTime(sub)

            self.__loadSubscribers()

            if self.sdEvent.start <= now:
                for sub in self.Subscribers:
                    if sub.nextCollectTime < now:
                        sub.sdProfile = self.buildProfile(sub)
                        self.collect(sub)
                        #self.clearChapterMissions(sub)
                        self.click(sub)
                        self.claimChapterRewards(sub)
                        self.upgradeMachineTier(sub)
                        self.setNextCollectTime(sub)

            # perform a check every 10 seconds
            time.sleep(10)


    def setNextCollectTime(self, sub:Subscriber):
        chapter = self.getSceneSettings(sub.sdProfile.chapter)
        targetXP = chapterMaxXP = chapter['max_exp']
        
        if (sub.sdProfile.chapter == self.getChapterCount() and 
            sub.sdProfile.exp == chapterMaxXP):
            sub.nextCollectTime = self.serverResetTime()
            print(f"{sub.username} next collect time: {datetime.datetime.fromtimestamp(sub.nextCollectTime)}, Finished the current event waiting till tomorrow!")
            return

        option = self.getClickOption(sub.sdProfile.chapter, sub.sdProfile.option)
        optionCost = option['item_cost'][0]['amount']
        optionXP = option['exp']

        if 'nextOptionAtExp' in option:
            targetXP = option['nextOptionAtExp']

        machine = self.getMachineSettings(sub.sdProfile.machineTier)
        productionCapTime = machine['max_explore_limit']
        productionInterval = machine['duration'] 
        productionCount = machine['reward_list'][0]['amount']

        # gets the time till next 
        standardTime = sub.lastClaimed + (productionCapTime - (productionInterval*2))

        deltaXP = targetXP - sub.sdProfile.exp
        deltaClicks = int(math.ceil(deltaXP/optionXP))
        deltaWine = deltaClicks*optionCost
        deltaIntervals = int(math.ceil(deltaWine/productionCount))

        deltaTime = sub.lastClaimed + (deltaIntervals * productionInterval)

        sub.nextCollectTime = standardTime
        if deltaTime < standardTime:
            sub.nextCollectTime = deltaTime

        print(f"{sub.username} next collect time: {datetime.datetime.fromtimestamp(sub.nextCollectTime)} --- delta time was: {datetime.datetime.fromtimestamp(deltaTime)} --- standard time was: {datetime.datetime.fromtimestamp(standardTime)}")



    """
        collects wine from the machine
    """

    def collect(self, sub: Subscriber):
        r = sub.network.event_sd_collect(self.sdEvent.id)
        sub.lastClaimed = r['server_time']

        #machine = self.getMachineSettings(sub.sdProfile.machineTier)
        #capTime = machine['max_explore_limit']
        #productionInterval = machine['duration']

        if r['success'] == True:
            #update the wine supply
            sub.sdProfile.wine = r['updated_item_list'][0]['amount']
            print(f"{sub.username} has (pre)collected {r['response']['reward_list'][0]['amount']} wine")
        else:
            # set the wine supply
            print(f"{sub.username} ERROR_WINE_COLLECT: [{r['error_code']}]: {r['error_message']}")


    """
        performs a click
    """
    def click(self, sub: Subscriber):
        chapter = self.getSceneSettings(sub.sdProfile.chapter)
        targetExp = chapterMaxExp = chapter['max_exp']

        option = self.getClickOption(sub.sdProfile.chapter, sub.sdProfile.option)
        optionCost = option['item_cost'][0]['amount']
        optionExp = option['exp']

        #if sub.sdProfile.exp == chapterMaxExp:
        #    print(f"{sub.username} has completed the current chapter already.")
        #    return False

        if 'nextOptionAtExp' in option:
            targetExp = option['nextOptionAtExp']

        # calculate the required clicks to reach the targetExp value
        delta = targetExp - sub.sdProfile.exp
        clicks = int(math.floor(sub.sdProfile.wine / optionCost))
        clicksRequired = int(math.ceil(delta / optionExp))

        print(f"{sub.username} option ID: {sub.sdProfile.option}, option cost: {optionCost}, option XP: {optionExp},  wine: {sub.sdProfile.wine}, xp: {sub.sdProfile.exp}, max xp: {chapterMaxExp}, target xp: {targetExp}, delta xp: {delta}, clicks: {clicks}, required clicks: {clicksRequired}")

        # do not uses more clicks than are required
        if clicksRequired < clicks:
            clicks = clicksRequired

        # perform click
        if clicks > 0:
            cost = optionCost*clicks
            r = sub.network.event_sd_click(
                self.sdEvent.id, 
                self.sdEvent.wineId, 
                sub.sdProfile.chapter, 
                sub.sdProfile.option, 
                cost, 
                clicks)

            if not r['success']:
                if 'DATING_REQUIREMENT_NOT_MATCH' == r['error_message']:
                    print(f"ERROR_ON_CLICK: {r['error_message']} The user [{sub.username}] needs to complete the story dialog")
                
                else:
                    print(f"ERROR_ON_CLICK: [{r['error_code']}] {r['error_message']}")
            else:
                # update the profile exp value
                clickXP = (clicks*optionExp)
                newXP = sub.sdProfile.exp + clickXP
                if newXP > chapterMaxExp:
                    newXP = chapterMaxExp

                print(f"{sub.username} clicks: {clicks} wine: -{cost} XP: +{clickXP}. Current XP: {sub.sdProfile.exp} -> {sub.sdProfile.exp}")
                sub.sdProfile.exp = newXP

    """
        WARNING DO NOT USE

        this will currently brick your progress for some reason.
    """
    def clearChapterMissions(self, sub:Subscriber):
        return
        messages = self.getStoryMessageSavePoints(sub.sdProfile.chapter)
        
        lastMessage = 0

        if sub.sdProfile.savePoint > lastMessage:
            lastMessage = sub.sdProfile.savePoint

        if sub.sdProfile.lastSelection > lastMessage:
            lastMessage = sub.sdProfile.lastSelection

        for message in messages:
            id = message['id']
            progress = message['progress_percent']
            if id < lastMessage:
                continue

            r = sub.network.event_sd_message_save_point(self.sdEvent.id, sub.sdProfile.chapter, id)
            
            if r['success'] == True:
                print(f"{sub.username} [{id}] saved dialog progress {progress}%")
            else:
                print(f"ERROR_ON_DIALOG_SAVE: [{r['error_code']}] {r['error_message']}")
                return

            choiceId = 0
            for selection in message['selection_list']:
                choiceId += 1
                if selection['correct'] == 1:
                    selectionId = selection['selection_id']
                    r = sub.network.event_sd_choose_message(self.sdEvent.id, sub.sdProfile.chapter, id, selectionId)

                    if r['success'] == True:
                        print(f"{sub.username} [{id}] chose dialog option {choiceId} '{selection['content']}'. progress {progress}")
                    else:
                        print(f"ERROR_ON_DIALOG_CHOOSE: [{r['error_code']}] {r['error_message']}")
                        return


    def claimChapterRewards(self, sub:Subscriber):
        chapter = self.getSceneSettings(sub.sdProfile.chapter)
        chapterMaxExp = chapter['max_exp']

        if sub.sdProfile.exp == chapterMaxExp:
            r = sub.network.event_sd_claim_chapter_rewards(
                self.sdEvent.id, sub.sdProfile.chapter)

            if r['success'] == True:
                sub.sdProfile = self.buildProfile(sub)
                print(f"{sub.username} claimed Chapter {sub.sdProfile.chapter} rewards")
            else:
                print(f"ERROR_ON_CLAIM_CHAPTER_REWARDS: [{r['error_code']}] {r['error_message']}")


    def upgradeMachineTier(self, sub:Subscriber):
        if sub.sdProfile.hurbs != None and sub.sdProfile.hurbs > 0:
            machine = self.getMachineSettings(sub.sdProfile.machineTier)
            upgrade = machine['upgrade_cost']
            if upgrade != None:
                if sub.sdProfile.hurbs >= upgrade[0]['amount']:
                    nextMachine = sub.sdProfile.machineTier+1
                    
                    r = sub.network.event_sd_purchase_machine(
                        self.sdEvent.id, 
                        nextMachine, 
                        upgrade)
                    
                    if r['success'] == True:
                        print(f"{sub.username} upgraded machine to tier {nextMachine} rewards")
                    else:
                        print(f"ERROR_ON_MACHINE_UPGRADE: [{r['error_code']}] {r['error_message']}")


e = EventManager()
e.run()
