class ImageFetchException(Exception):
    """
    Raised when the image can not be fetched from the AI deck
    """
    pass


class DeckException(Exception):
    """
    Raised when a at least on of the expansion decks are not detected
    """
    pass


class BatteryException(Exception):
    """
    Raised when the battery level is too low
    """
    def __init__(self, battery_level, cf_takeoff):
        """
         constructor for a crazyflie object
        :param battery_level: voltage level of the crazyflie
        :param cf_takeoff: Boolean variable to mark if cf took of or not (True -> cf took off)
        """
        self.battery_level = battery_level
        self.cf_takeoff = cf_takeoff