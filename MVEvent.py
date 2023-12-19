class MVEvent:
    def __init__(self, event, settings):
        self.hasBeenSeen = False

        self.id = event['event_id']
        self.version = event['version_id']
        self.pet = event['pet_id']
        self.start = event['timeslot_detail'][0]['start_time']
        self.end = event['timeslot_detail'][0]['end_time']

        for level in settings['multiverse_dating_level_settings']:
            if level["event_id"] != self.id:
                continue
            if level['level'] == 2:
                self.crystalId = level['reward_list'][0]['asset_id']
                break

        for explore in settings['multiverse_dating_explore_item_settings']:
            if explore['event_id'] != self.id:
                continue
            self.wineId = explore['reward_list'][0]['asset_id']
            break


        self.settings = settings


class MVProfile:
    level = None
    exp = None
    option = None
    machineTier = None
    question = None
    wine = None
    crystals = None

    savePoint = None
