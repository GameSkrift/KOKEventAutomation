class SDEvent:
    def __init__(self, event, settings):
        self.hasBeenSeen = False

        self.id = event['event_id']
        self.type = event['event_type']
        self.name = event['name']
        self.version = event['version_id']
        self.pet = event['pet_id']
        self.start = event['timeslot_detail'][0]['start_time']
        self.end = event['timeslot_detail'][0]['end_time']

        for chapter in settings['explore_item_settings']:
            if chapter["event_id"] != self.id or len(chapter['cost_list']) == 0:
                continue
            self.wineId = chapter['reward_list'][0]['asset_id']
            self.herbsId = chapter['cost_list'][0]['asset_id']
            break


        self.settings = settings


class SDProfile:
    chapter = None
    exp = None
    option = None
    machineTier = None
    wine = None
    hurbs = None

    savePoint = None
    lastSelection = None

