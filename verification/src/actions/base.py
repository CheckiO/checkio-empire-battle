from .exceptions import ActionValidateError
from tools.distances import euclidean_distance


class BaseItemActions(object):
    def __init__(self, item, fight_handler):
        self._item = item
        self._fight_handler = fight_handler
        self._actions = self.actions_init()

    def actions_init(self):
        """
        add actions for custom class
        :return:
        """
        return {
            'attack': self.action_attack
        }

    def action_attack(self, data):
        enemy = self._fight_handler.fighters.get(data['id'])
        if enemy.is_dead:
            return {"action": "stand"}
        if enemy is None:
            raise Exception("No enemy")
            return  # WTF

        return self._shot(enemy)

    def _shot(self, enemy):
        attacker = self._item
        attacker.charging += self._fight_handler.GAME_FRAME_TIME * attacker.rate_of_fire
        if attacker.charging < 1:
            return {'action': 'charging'}

        enemy.health -= attacker.damage_per_shot
        if enemy.health <= 0:
            self._dead(enemy)

        attacker.charging -= 1
        return {
            'action': 'attack',
            'aid': enemy.id,
            'damaged': [enemy.id],  # TODO:
        }

    def _dead(self, enemy):
        enemy.set_state_dead()
        self._fight_handler.send_death_event(enemy.id)
        self._fight_handler.unsubscribe(enemy)

    def parse_action_data(self, action, data):
        if action not in self._actions:
            raise NotImplementedError  # TODO: custom exception

        validator = getattr(self, 'validate_{}'.format(action))
        if validator is not None:
            validator(action, data)

        return {
            'name': action,
            'data': data,
        }

    def validate_attack(self, action, data):
        enemy = self._fight_handler.fighters.get(data['id'])
        if enemy.player['id'] == self._item.player['id']:
            raise ActionValidateError("Can not attack own item")

        distance_to_enemy = euclidean_distance(enemy.coordinates, self._item.coordinates)
        item_firing_range = self._item.firing_range
        if distance_to_enemy - enemy.size / 2 > item_firing_range:
            raise ActionValidateError("Can not attack item, it's big distance")

    def validate_move(self, action, data):
        if not self._fight_handler.is_point_on_map(*data["coordinates"]):
            raise ActionValidateError("Wrong coordinates")

    def do_action(self, action_data):
        action_handler = self._actions[action_data['name']]
        return action_handler(action_data['data'])
