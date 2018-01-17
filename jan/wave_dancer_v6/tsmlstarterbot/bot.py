import heapq
import numpy as np
import os
import time
import logging

import hlt

import sys

from tsmlstarterbot.common import *
from tsmlstarterbot.neural_net import NeuralNet



#####################
### Ugly solution ###
#####################

# def get_closest_enemy_ships(self, ship):
#     all_enemy_ships = [enemy_ship for enemy_ship in game_map._all_ships() if enemy_ship not in team_ships and enemy_ship.id != ship.id]
#     enemy_ships_nearby = [enemy_ship for enemy_ship in game_map._all_ships() if enemy_ship not in initial_team_ships and ship.calculate_distance_between(enemy_ship) < 30]


# class Flock:
    
#     def __init__(self, members, closest_enemy_ships):
#         self.members = members
#         self.closest_enemy_ships


#     initial_team_ships = [team_ship for team_ship in game_map.get_me().all_ships()]
#     enemy_ships_nearby = [enemy_ship for enemy_ship in game_map._all_ships() if enemy_ship not in initial_team_ships and ship.calculate_distance_between(enemy_ship) < 40]
#     closest_enemy_ships = []

#     current -> array[Enemy_ships]

#     self.members
#         initial_team_ships = [team_ship for team_ship in game_map.get_me().all_ships()]
#         team_ships = []
#         for team_ship in initial_team_ships:
#             if team_ship.id != ship.id:
#                 team_ships.append(team_ship)

#         team_ships_nearby = [team_ship for team_ship in team_ships if ship.calculate_distance_between(team_ship) < 50]
        
#         closest_enemy_ship_distance = 1000
#         closest_enemy_ship = all_enemy_ships[0]

#     def get_closest_enemy_ship:
#         self.members[0].calculate_distance_between(closest_enemy_ships[0])



class Entity:
   

    def __init__(self, x, y, radius, health, player, entity_id):
        self.x = x
        self.y = y
        self.radius = radius
        self.health = health
        self.owner = player
        self.id = entity_id

    def calculate_distance_between(self, target):
        """
        Calculates the distance between this object and the target.
        :param Entity target: The target to get distance to.
        :return: distance
        :rtype: float
        """
        return math.sqrt((target.x - self.x) ** 2 + (target.y - self.y) ** 2)

    def calculate_angle_between(self, target):
        """
        Calculates the angle between this object and the target in degrees.
        :param Entity target: The target to get the angle between.
        :return: Angle between entities in degrees
        :rtype: float
        """
        return math.degrees(math.atan2(target.y - self.y, target.x - self.x)) % 360

    def closest_point_to(self, target, min_distance=3):
        """
        Find the closest point to the given ship near the given target, outside its given radius,
        with an added fudge of min_distance.
        :param Entity target: The target to compare against
        :param int min_distance: Minimum distance specified from the object's outer radius
        :return: The closest point's coordinates
        :rtype: Position
        """
        angle = target.calculate_angle_between(self)
        radius = target.radius + min_distance
        x = target.x + radius * math.cos(math.radians(angle))
        y = target.y + radius * math.sin(math.radians(angle))

        return Position(x, y)

    def _link(self, players, planets):
        pass

    def __str__(self):
        return "Entity {} (id: {}) at position: (x = {}, y = {}), with radius = {}"\
            .format(self.__class__.__name__, self.id, self.x, self.y, self.radius)

    def __repr__(self):
        return self.__str__()



class Position(Entity):
    """
    A simple wrapper for a coordinate.

    Intended to be passed to some functions in place of a ship or planet.
    :ivar id: Unused
    :ivar x: The x-coordinate.
    :ivar y: The y-coordinate.
    :ivar radius: The position's radius (should be 0).
    :ivar health: Unused.
    :ivar owner: Unused.
    """

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 0
        self.health = None
        self.owner = None
        self.id = None

    def _link(self, players, planets):
        raise NotImplementedError("Position should not have link attributes.")


class FuturePosition:
    def __init__(self, ship_id, Position):
        self.ship_id = ship_id
        self.Position = Position


class Bot:
    def __init__(self, location, name):
        current_directory = os.path.dirname(os.path.abspath(__file__))
        model_location = os.path.join(current_directory, os.path.pardir, "models", location)
        self._name = name
        self._neural_net = NeuralNet(cached_model=model_location)

        # Run prediction on random data to make sure that code path is executed at least once before the game starts
        random_input_data = np.random.rand(PLANET_MAX_NUM, PER_PLANET_FEATURES)
        predictions = self._neural_net.predict(random_input_data)
        assert len(predictions) == PLANET_MAX_NUM

    def play(self):
        """
        Play a game using stdin/stdout.
        """

        # Initialize the game.
        game = hlt.Game(self._name)

        while True:
            # Update the game map.
            game_map = game.update_map()
            start_time = time.time()

            # Produce features for each planet.
            features = self.produce_features(game_map)
            
            # Find predictions which planets we should send ships to.
            predictions = self._neural_net.predict(features)

            # Use simple greedy algorithm to assign closest ships to each planet according to predictions.
            ships_to_planets_assignment = self.produce_ships_to_planets_assignment(game_map, predictions)

            # Produce halite instruction for each ship.
            instructions = self.produce_instructions(game_map, ships_to_planets_assignment, start_time)

            # Send the command.
            game.send_command_queue(instructions)

    def produce_features(self, game_map):
        """
        For each planet produce a set of features that we will feed to the neural net. We always return an array
        with PLANET_MAX_NUM rows - if planet is not present in the game, we set all featurse to 0.

        :param game_map: game map
        :return: 2-D array where i-th row represents set of features of the i-th planet
        """
        feature_matrix = [[0 for _ in range(PER_PLANET_FEATURES)] for _ in range(PLANET_MAX_NUM)]

        for planet in game_map.all_planets():

            # Compute "ownership" feature - 0 if planet is not occupied, 1 if occupied by us, -1 if occupied by enemy.
            if planet.owner == game_map.get_me():
                ownership = 1
            elif planet.owner is None:
                ownership = 0
            else:  # owned by enemy
                ownership = -1

            my_best_distance = 10000
            enemy_best_distance = 10000

            gravity = 0

            health_weighted_ship_distance = 0
            sum_of_health = 0

            for player in game_map.all_players():
                for ship in player.all_ships():
                    d = ship.calculate_distance_between(planet)
                    if player == game_map.get_me():
                        my_best_distance = min(my_best_distance, d)
                        sum_of_health += ship.health
                        health_weighted_ship_distance += d * ship.health
                        gravity += ship.health / (d * d)
                    else:
                        enemy_best_distance = min(enemy_best_distance, d)
                        gravity -= ship.health / (d * d)

            distance_from_center = distance(planet.x, planet.y, game_map.width / 2, game_map.height / 2)

            health_weighted_ship_distance = health_weighted_ship_distance / sum_of_health

            remaining_docking_spots = planet.num_docking_spots - len(planet.all_docked_ships())
            signed_current_production = planet.current_production * ownership

            is_active = remaining_docking_spots > 0 or ownership != 1

            feature_matrix[planet.id] = [
                planet.health,
                remaining_docking_spots,
                planet.remaining_resources,
                signed_current_production,
                gravity,
                my_best_distance,
                enemy_best_distance,
                ownership,
                distance_from_center,
                health_weighted_ship_distance,
                is_active
            ]

        return feature_matrix


    ###########################
    ### Collision Avoidance ###
    ###########################
    def compute_future_position(self, active_ship, target):
        logging.info("target")
        logging.info(target)
        delta_x = 0
        delta_y = 0
        delta_z = active_ship.calculate_distance_between(target)
        logging.info("delta_Z")
        logging.info(delta_z)
        alpha = active_ship.calculate_angle_between(target)
        logging.info("alpha")
        logging.info(alpha)
        beta = 90 - alpha
        gamma = 90

        delta_x = math.cos(alpha) * delta_z
        delta_y = math.sin(beta) * delta_z

        new_position = Position(x = active_ship.x + delta_x, y = active_ship.y + delta_y)

        t = math.pow(math.cos(alpha) * delta_z, 2) + math.pow(math.sin(beta) * delta_z ,2 )
        logging.info('result')
        logging.info(math.sqrt(t)) 
        
        logging.info("Current Position")
        logging.info(active_ship.id)
        logging.info(active_ship.x)
        logging.info(active_ship.y)

        logging.info("New Position")
        logging.info(active_ship.id)
        logging.info(new_position.x)
        logging.info(new_position.y)

        logging.info("Future Postion after compute future position")
        logging.info(new_position)
        return new_position

    ##################################
    ### End of Collision Avoidance ###
    ##################################

    def produce_ships_to_planets_assignment(self, game_map, predictions):
        """
        Given the predictions from the neural net, create assignment (undocked ship -> planet) deciding which
        planet each ship should go to. Note that we already know how many ships is going to each planet
        (from the neural net), we just don't know which ones.

        :param game_map: game map
        :param predictions: probability distribution describing where the ships should be sent
        :return: list of pairs (ship, planet)
        """
        undocked_ships = [ship for ship in game_map.get_me().all_ships()
                          if ship.docking_status == ship.DockingStatus.UNDOCKED]




        ##################################
        ### Code base for futher usage ###
        ##################################
        team_ships = game_map.get_me().all_ships()
        enemy_ships = [ship for ship in game_map._all_ships() if ship not in team_ships]

        ####################
        ### General Idea ###
        ####################
        # Learn how to avoid battles unless you are in a superior position
        # running away
        # group
        # attack

        # greedy assignment
        assignment = []
        number_of_ships_to_assign = len(undocked_ships)

        if number_of_ships_to_assign == 0:
            return []

        planet_heap = []
        ship_heaps = [[] for _ in range(PLANET_MAX_NUM)]

        # Create heaps for greedy ship assignment.
        for planet in game_map.all_planets():
            # We insert negative number of ships as a key, since we want max heap here.
            heapq.heappush(planet_heap, (-predictions[planet.id] * number_of_ships_to_assign, planet.id))
            h = []
            for ship in undocked_ships:
                d = ship.calculate_distance_between(planet)
                heapq.heappush(h, (d, ship.id))
            ship_heaps[planet.id] = h

        # Create greedy assignment
        already_assigned_ships = set()

        while number_of_ships_to_assign > len(already_assigned_ships):
            # Remove the best planet from the heap and put it back in with adjustment.
            # (Account for the fact the distribution values are stored as negative numbers on the heap.)
            ships_to_send, best_planet_id = heapq.heappop(planet_heap)
            ships_to_send = -(-ships_to_send - 1)
            heapq.heappush(planet_heap, (ships_to_send, best_planet_id))

            # Find the closest unused ship to the best planet.
            _, best_ship_id = heapq.heappop(ship_heaps[best_planet_id])
            while best_ship_id in already_assigned_ships:
                _, best_ship_id = heapq.heappop(ship_heaps[best_planet_id])

            # Assign the best ship to the best planet.
            assignment.append(
                (game_map.get_me().get_ship(best_ship_id), game_map.get_planet(best_planet_id)))
            already_assigned_ships.add(best_ship_id)

        return assignment

    def produce_instructions(self, game_map, ships_to_planets_assignment, round_start_time):
        """
        Given list of pairs (ship, planet) produce instructions for every ship to go to its respective planet.
        If the planet belongs to the enemy, we go to the weakest docked ship.
        If it's ours or is unoccupied, we try to dock.

        :param game_map: game map
        :param ships_to_planets_assignment: list of tuples (ship, planet)
        :param round_start_time: time (in seconds) between the Epoch and the start of this round
        :return: list of instructions to send to the Halite engine
        """
        command_queue = []
        future_positions = []
        # Send each ship to its planet

        ######################################################
        ### Undock Mechanic in case of a nearby enemy ship ###
        ######################################################
        
        # Kind of useless

        ##############################
        ### End of Undock Mechanic ###
        ##############################


       

        target_planet = None
        filtered_planets_by_distance = []
        distance_to_next_planet = 1000

        for ship, planet in ships_to_planets_assignment:
            entities_by_distance = game_map.nearby_entities_by_distance(ship)
            for distance in sorted(entities_by_distance):
                nearest_planet = next((nearest_entity for nearest_entity in entities_by_distance[distance] if isinstance(nearest_entity, hlt.entity.Planet)), None)
                if nearest_planet != None:                       
                    filtered_planets_by_distance.append(nearest_planet)
                    if distance_to_next_planet > ship.calculate_distance_between(nearest_planet):
                        distance_to_next_planet = ship.calculate_distance_between(nearest_planet)
                        target_planet = nearest_planet
                        distance = 1000        

        for ship, planet in ships_to_planets_assignment:

            # Distance to the closest enemy ship
            distance_to_next_enemy_ship = 1000
            # Default ship movement speed
            speed = hlt.constants.MAX_SPEED

            # Checking whether a planet is free to be settled
            is_planet_friendly = not planet.is_owned() or planet.owner == game_map.get_me()

            ##############################
            ### Mandatory calculations ###
            ##############################
            initial_team_ships = [team_ship for team_ship in game_map.get_me().all_ships()]
            team_ships = []
            for team_ship in initial_team_ships:
                if team_ship.id != ship.id:
                    team_ships.append(team_ship)

            all_enemy_ships = [enemy_ship for enemy_ship in game_map._all_ships() if enemy_ship not in team_ships and enemy_ship.id != ship.id]
            enemy_ships_nearby = [enemy_ship for enemy_ship in game_map._all_ships() if enemy_ship not in initial_team_ships and ship.calculate_distance_between(enemy_ship) < 40]
            team_ships_nearby = [team_ship for team_ship in team_ships if ship.calculate_distance_between(team_ship) < 50]
            
            closest_enemy_ship_distance = 1000
            closest_enemy_ship = all_enemy_ships[0]
            for enemy_ship in enemy_ships_nearby:
                if ship.calculate_distance_between(enemy_ship) < closest_enemy_ship_distance:
                    closest_enemy_ship_distance = ship.calculate_distance_between(enemy_ship)
                    closest_enemy_ship = enemy_ship

            closest_start_enemy_ship_distance = 1000
            closest_start_target = all_enemy_ships[0]
            for enemy_ship in all_enemy_ships:
                if ship.calculate_distance_between(enemy_ship) < closest_start_enemy_ship_distance:
                    closest_start_enemy_ship_distance = ship.calculate_distance_between(enemy_ship)
                    closest_start_target = enemy_ship

            closest_team_ship_distance = 1000
            closest_team_ship = None
            for team_ship in team_ships_nearby:
                if ship.calculate_distance_between(team_ship) < closest_team_ship_distance:
                    closest_team_ship_distance = ship.calculate_distance_between(team_ship)
                    closest_team_ship = team_ship

            ###################################
            ### Initial Harassment Mechanic ###
            ###################################

            # First Turn
            if ship.id == 0 and closest_start_enemy_ship_distance < 95:
                logging.info("Initial Harassment Mechanic Active")
                logging.info(closest_start_target)
                command_queue.append(
                    self.navigate(game_map, round_start_time, ship, ship.closest_point_to(closest_start_target), speed))
            
            ##########################################
            ### End of Initial Harassment Mechanic ###
            ##########################################


            ################
            ### Flocking ###
            ################
            # if closest_enemy_ship_distance < 20:
            # # elif True:
            
            #     if closest_team_ship != None:
                
            #         # logging.info("ship.position")
            #         # logging.info(ship.x)
            #         # logging.info(ship.y)
            #         # target = Position(ship.x, ship.y)

            #         # logging.info('New Position')
            #         # logging.info(target)


            #         future_position_map = []
            #         # newFuturePosition = self.get(ship, Position(0,0))
            #         #new_future_position = FuturePosition(ship.id, Position(ship.x + delta_x, ship.y + delta_y))

            #         navigation_target = Position(closest_team_ship.x + 0.6, closest_team_ship.y + 0.6)
            #         navigation_target = self.avoidCollision(self, ship, navigation_target, future_positions)
            #         future_position = self.compute_future_position(ship, navigation_target)
            #         future_positions.append(future_position)
            #         logging.info('flocking was triggered')
            #         command_queue.append(
            #             self.navigate(game_map, round_start_time, ship, future_position, speed))    

        

            #######################
            ### End of Flocking ###
            #######################


            ###################################
            ### Mining Ship Attack Mechanic ###
            ###################################
            # elif closest_enemy_ship_distance < 10 and closest_enemy_ship.DockingStatus.DOCKED:
            #     logging.info("Attack closeby mining ship Mechanic Active")
            #     command_queue.append(
            #         self.navigate(game_map, round_start_time, ship, ship.closest_point_to(closest_enemy_ship), speed))    

            ##########################################
            ### End of Mining Ship Attack Mechanic ###
            ##########################################

           


            #######################
            ### Combat Mechanic ###
            #######################
            elif closest_enemy_ship_distance < 30:

                initial_team_ships = [team_ship for team_ship in game_map.get_me().all_ships()]
                team_ships = []
                for team_ship in initial_team_ships:
                    if team_ship.id != ship.id:
                        team_ships.append(team_ship)

                all_enemy_ships = [enemy_ship for enemy_ship in game_map._all_ships() if enemy_ship not in team_ships and enemy_ship.id != ship.id]
                enemy_ships_nearby = [enemy_ship for enemy_ship in game_map._all_ships() if enemy_ship not in initial_team_ships and ship.calculate_distance_between(enemy_ship) < 40]
                team_ships_nearby = [team_ship for team_ship in team_ships if ship.calculate_distance_between(team_ship) < 50]
                
                closest_enemy_ship_distance = 1000
                closest_enemy_ship = all_enemy_ships[0]
                for enemy_ship in enemy_ships_nearby:
                    if ship.calculate_distance_between(enemy_ship) < closest_enemy_ship_distance:
                        closest_enemy_ship_distance = ship.calculate_distance_between(enemy_ship)
                        closest_enemy_ship = enemy_ship

                closest_start_enemy_ship_distance = 1000
                closest_start_target = all_enemy_ships[0]
                for enemy_ship in all_enemy_ships:
                    if ship.calculate_distance_between(enemy_ship) < closest_start_enemy_ship_distance:
                        closest_start_enemy_ship_distance = ship.calculate_distance_between(enemy_ship)
                        closest_start_target = enemy_ship

                closest_team_ship_distance = 1000
                closest_team_ship = None
                for team_ship in team_ships_nearby:
                    if ship.calculate_distance_between(team_ship) < closest_team_ship_distance:
                        closest_team_ship_distance = ship.calculate_distance_between(team_ship)
                        closest_team_ship = team_ship

                ###################################
                ### Initial Harassment Mechanic ###
                ###################################
                logging.info(closest_team_ship)
                if closest_team_ship_distance > 5: 
                    if closest_team_ship != None:
                        logging.info('Find a friend')

                        navigation_target = Position(closest_team_ship.x + 1, closest_team_ship.y + 1)
                        logging.info('Old Navigation Target')
                        logging.info(navigation_target)

                        for counter in range(0, len(future_positions)-1):
                            # logging.info(future_positions[counter])
                            if (future_positions[counter].x < navigation_target.x + 0.5 or future_positions[counter].x > navigation_target.x - 0.5) and (future_positions[counter].y < navigation_target.y +0.5 or future_positions[counter].y > navigation_target.y-0.5):
                                navigation_target = Position(navigation_target.x + 1, navigation_target.y + 1)
                                counter = 0
                        logging.info('Nehmen wir immer noch uns selbst?')
                        logging.info(navigation_target)
                        future_position = self.compute_future_position(ship, navigation_target)
                        future_positions.append(future_position)
                        
                        command_queue.append(
                            self.navigate(game_map, round_start_time, ship, navigation_target, speed))

                else:
                    
                    navigation_target = Position(closest_enemy_ship.x, closest_enemy_ship.y)

                    for counter in range(0, len(future_positions)-1):
                            if (future_positions[counter].x < navigation_target.x + 0.5 or future_positions[counter].x > navigation_target.x - 0.5) and (future_positions[counter].y < navigation_target.y +0.5 or future_positions[counter].y > navigation_target.y-0.5):
                                navigation_target = Position(navigation_target.x + 1, navigation_target.y + 1)
                            counter = 0

                    future_position = self.compute_future_position(ship, navigation_target)
                    future_positions.append(future_position)

                    logging.info('attack')
                    command_queue.append(
                        self.navigate(game_map, round_start_time, ship, navigation_target, speed))      
                                
            ##############################
            ### End of Combat Mechanic ###
            ##############################


            ##########################################################
            ### Settling Mechanic if there is no enemy ship nearby ###
            ##########################################################
            elif is_planet_friendly:
                if ship.can_dock(planet):
                    if closest_enemy_ship_distance > 15:
                        logging.info("Settle")
                        command_queue.append(ship.dock(planet))
                        
            ################################
            ### End of Settling Mechanic ###
            ################################

                else:
                    logging.info('default behaviour')
                    command_queue.append(
                        self.navigate(game_map, round_start_time, ship, ship.closest_point_to(planet), speed))
            else:
                docked_ships = planet.all_docked_ships()
                assert len(docked_ships) > 0
                weakest_ship = None
                for s in docked_ships:
                    if weakest_ship is None or weakest_ship.health > s.health:
                        weakest_ship = s
                command_queue.append(
                    self.navigate(game_map, round_start_time, ship, ship.closest_point_to(weakest_ship), speed))
        return command_queue

    def navigate(self, game_map, start_of_round, ship, destination,  speed):
        """
        Send a ship to its destination. Because "navigate" method in Halite API is expensive, we use that method only if
        we haven't used too much time yet.

        :param game_map: game map
        :param start_of_round: time (in seconds) between the Epoch and the start of this round
        :param ship: ship we want to send
        :param destination: destination to which we want to send the ship to
        :param speed: speed with which we would like to send the ship to its destination
        :return:
        """
        current_time = time.time()
        have_time = current_time - start_of_round < 1.2
        navigate_command = None
        if have_time:
            navigate_command = ship.navigate(destination, game_map, speed=speed, max_corrections=180)
        if navigate_command is None:
            # ship.navigate may return None if it cannot find a path. In such a case we just thrust.
            dist = ship.calculate_distance_between(destination)
            speed = speed if (dist >= speed) else dist
            navigate_command = ship.thrust(speed, ship.calculate_angle_between(destination))
        return navigate_command
