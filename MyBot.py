"""
Welcome to your first Halite-II bot!

This bot's name is Settler. It's purpose is simple (don't expect it to win complex games :) ):
1. Initialize game
2. If a ship is not docked and there are unowned planets
2.a. Try to Dock in the planet if close enough
2.b If not, go towards the planet

Note: Please do not place print statements here as they are used to
communicate with the Halite engine. If you need
to log anything use the logging module.
"""

import hlt
import logging
from collections import OrderedDict
game = hlt.Game("battleBot")
logging.info("Starting battleBot")

# Custom Impots
from collections import OrderedDict

while True:
    game_map = game.update_map()
    command_queue = []
    
    for ship in game_map.get_me().all_ships():
        shipid = ship.id
        if ship.docking_status != ship.DockingStatus.UNDOCKED:
            # Skip this ship
            continue

        entities_by_distance = game_map.nearby_entities_by_distance(ship)
        entities_by_distance = OrderedDict(sorted(entities_by_distance.items(), key=lambda t: t[0]))
        
        closest_empty_planets = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Planet) and not entities_by_distance[distance][0].is_owned()]

        team_ships = game_map.get_me().all_ships()
        closest_enemy_ships = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Ship) and entities_by_distance[distance][0] not in team_ships]

        # harass
        if (true):
            
            # Attack enemy ships currently mining
            # if len(closest_enemy_ships) > 0:
                
                # target_ship = closest_enemy_ships[0]
                
                # for enemy_ship in closest_enemy_ships:
                #     if enemy_ship.docking_status != ship.DockingStatus.UNDOCKED:
                        
                #         navigate_command = ship.navigate(
                #             ship.closest_point_to(enemy_ship),
                #             game_map,
                #             speed=int(hlt.constants.MAX_SPEED),
                #             ignore_ships=False)

                #         if navigate_command:
                #             command_queue.append(navigate_command)
                #             break

        else:
            # If there are any empty planets, let's try to mine!
            if len(closest_empty_planets) > 0:
                target_planet = closest_empty_planets[0]
                if ship.can_dock(target_planet):
                    command_queue.append(ship.dock(target_planet))
                else:
                    navigate_command = ship.navigate(
                                ship.closest_point_to(target_planet),
                                game_map,
                                speed=int(hlt.constants.MAX_SPEED),
                                ignore_ships=False)

                    if navigate_command:
                        command_queue.append(navigate_command)

            # FIND SHIP TO ATTACK!
            # elif len(closest_enemy_ships) > 0:
            #     target_ship = closest_enemy_ships[0]
            #     navigate_command = ship.navigate(
            #                 ship.closest_point_to(target_ship),
            #                 game_map,
            #                 speed=int(hlt.constants.MAX_SPEED),
            #                 ignore_ships=False)

            #     if navigate_command:
            #         command_queue.append(navigate_command)


            # Attack enemy ships currently mining
            elif len(closest_enemy_ships) > 0:
                
                target_ship = closest_enemy_ships[0]
                
                for enemy_ship in closest_enemy_ships:
                    if enemy_ship.docking_status != ship.DockingStatus.UNDOCKED:
                        
                        navigate_command = ship.navigate(
                            ship.closest_point_to(enemy_ship),
                            game_map,
                            speed=int(hlt.constants.MAX_SPEED),
                            ignore_ships=False)

                        if navigate_command:
                            command_queue.append(navigate_command)
                            break
                        
                            
    game.send_command_queue(command_queue)
    # TURN END
# GAME END
