import requests
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import UserUtteranceReverted, SlotSet, FollowupAction
import re

class ActionAskLanguage(Action):
    def name(self) -> Text:
        return "action_ask_language"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        messages = [
            "What language would you like to use?",
            "You can choose from English, Japanese, or Chinese.",
            "Please type your preferred language."
        ]

        for message in messages:
            dispatcher.utter_message(text=message)

        return []


class ActionWelcome(Action):

    def name(self) -> Text:
        return "action_welcome"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        messages = [
            "Welcome to Easy Cinema!",
            "How may I assist you today?"
        ]

        for message in messages:
            dispatcher.utter_message(text=message)

        return []


class ActionSetLanguage(Action):
    def name(self):
        return "action_set_language"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        selected_language = tracker.latest_message['text'].lower()

        if "english" in selected_language:
            dispatcher.utter_message(response="utter_english_selected")
        elif "japanese" in selected_language:
            dispatcher.utter_message(response="utter_japanese_selected")
        elif "chinese" in selected_language:
            dispatcher.utter_message(response="utter_chinese_selected")
        else:
            dispatcher.utter_message(text="Sorry, I didn't understand that.")
            dispatcher.utter_message(
                text="It seems like your message got cut off.")
            dispatcher.utter_message(
                text="Could you please provide more details or clarify what you meant?")
            dispatcher.utter_message(
                text="Could you please choose from English, Japanese, or Chinese?")
            dispatcher.utter_message(
                text="I'm here to help with any inquiries about our Athena bot service! 😊")
            return [UserUtteranceReverted()]

        return []


class ActionChooseOption(Action):
    def name(self) -> Text:
        return "action_choose_option"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        latest_message = tracker.latest_message.get('text', '').lower()

        movie_keywords = ["movie", "ticket", "mov"]
        cinema_keywords = ["cinema", "location", "where", "cin"]

        selected_option = None
        if any(keyword in latest_message for keyword in movie_keywords):
            selected_option = "movies"
        elif any(keyword in latest_message for keyword in cinema_keywords):
            selected_option = "cinemas"

        if selected_option == "movies":
            dispatcher.utter_message(
                text="You have selected movies. Here are the available options:",
                buttons=[
                    {"title": "Zodiac", "payload": "/set_movie{\"movie\":\"Zodiac\"}"},
                    {"title": "Constantine",
                        "payload": "/set_movie{\"movie\":\"Constantine\"}"}
                ]
            )
            return [SlotSet("choice", "movies")]
        elif selected_option == "cinemas":
            dispatcher.utter_message(response="utter_ask_location")
            return [SlotSet("choice", "cinemas")]
        else:
            dispatcher.utter_message(text="Sorry, I didn't understand that.")
            dispatcher.utter_message(
                text="It seems like your message got cut off.")
            dispatcher.utter_message(
                text="Could you please provide more details or clarify what you meant?")
            dispatcher.utter_message(
                text="Please choose 'Movies' or 'Cinemas'.")
            dispatcher.utter_message(
                text="I'm here to help with any inquiries about our Athena bot service! 😊")
            return [UserUtteranceReverted()]

        return []

class ActionDetectBookingKeywords(Action):
    def name(self):
        return "action_detect_booking_keywords"

    def run(self, dispatcher, tracker, domain):
        user_message = tracker.latest_message.get("text", "").lower()

        # Define keywords to look for
        keywords = ["movie", "book", "ticket", "film", "show"]
        detected_keywords = [word for word in keywords if word in user_message]

        # Respond if keywords are found
        if detected_keywords:
            dispatcher.utter_message(
                text=f"I see you want to book a show. Let's proceed!"
            )
            # Trigger the movie booking flow
            return [FollowupAction("action_fetch_movies")]
        else:
            dispatcher.utter_message(
                text="Sorry, I couldn't understand your request. Could you clarify?"
            )
            # Revert the user's input if no relevant keywords are found
            return [UserUtteranceReverted()]


class ActionFetchMovies(Action):
    def name(self):
        return "action_fetch_movies"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        import requests

        api_key = "f49245f9014c10013d784a78dd686b44"
        base_url = "https://api.themoviedb.org/3"

        # Define the movies to fetch
        movies_to_fetch = ["Zodiac", "Constantine"]

        # Custom poster URLs
        custom_posters = {
            "Zodiac": "https://i.pinimg.com/736x/08/8c/43/088c43d5a8e9d47d2ea03719062699cf.jpg",
            "Constantine": "https://media.posterlounge.com/img/products/760000/759054/759054_poster.jpg"
        }

        movie_details = []

        for movie in movies_to_fetch:
            search_url = f"{base_url}/search/movie?api_key={api_key}&query={movie}"
            response = requests.get(search_url)
            results = response.json().get('results', [])

            if results:
                movie_info = results[0]
                movie_title = movie_info['title']
                movie_description = movie_info['overview']

                # Use custom poster if available, otherwise fetch from TMDB
                movie_poster = custom_posters.get(
                    movie_title,
                    f"https://image.tmdb.org/t/p/w500{movie_info['poster_path']}" if movie_info.get('poster_path') else None
                )

                movie_details.append(
                    (movie_title, movie_description, movie_poster))

        if movie_details:
            # Send details for each movie
            for index, (title, description, poster) in enumerate(movie_details, start=1):
                # Group title and description together
                movie_message = f"{index}. {title}\nDescription: {description}"
                dispatcher.utter_message(text=movie_message)

                # Send poster image
                if poster:
                    dispatcher.utter_message(image=poster)

            # Send a final prompt for user choice
            dispatcher.utter_message(
                text="Please reply with the number of your choice (e.g., 1 for Zodiac, 2 for Constantine)."
            )
        else:
            dispatcher.utter_message(
                text="Sorry, I couldn't fetch the movie details."
            )

        return []

class ActionSendMovieTemplate(Action):
    def name(self):
        return "action_send_movie_template"

    def run(self, dispatcher: CollectingDispatcher, tracker, domain):
        dispatcher.utter_message(
            json_message={
                "type": "template",
                "template_name": "moviechoice",
                "language": "en",
                "parameters": []
            }
        )
        return []


class ActionSetMovie(Action):
    def name(self):
        return "action_set_movie"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        # Movie mapping
        movie_mapping = {
            "1": "Zodiac",
            "2": "Constantine"
        }

        # Get user input
        user_input = tracker.latest_message.get("text", "").lower()

        # Try to match a number first
        import re
        match = re.search(r"\b(1|2)\b", user_input)  # Matches "1" or "2"

        if match:
            movie_number = match.group(1)  # Extract the matched number
            selected_movie = movie_mapping.get(movie_number)

            if selected_movie:
                # If valid movie, confirm and set the slot
                dispatcher.utter_message(
                    text=f"You have selected {selected_movie}."
                )
                dispatcher.utter_message(
                    text="Please select the desired time for the show."
                )
                return [SlotSet("movie", selected_movie), FollowupAction("action_fetch_showtimes")]
            else:
                dispatcher.utter_message(
                    text="Sorry, I couldn't find a movie for that choice. Please try again."
                )
                return [UserUtteranceReverted()]
        else:
            # If no number is matched, search for the movie name
            for movie_number, movie_name in movie_mapping.items():
                if movie_name.lower() in user_input:
                    dispatcher.utter_message(
                        text=f"You have selected {movie_name}."
                    )
                    dispatcher.utter_message(
                        text="Please select the desired time for the show."
                    )
                    return [SlotSet("movie", movie_name), FollowupAction("action_fetch_showtimes")]

            # If neither number nor movie name is found
            dispatcher.utter_message(text="Sorry, I didn't understand that.")
            dispatcher.utter_message(
                text="It seems like your message got cut off."
            )
            dispatcher.utter_message(
                text="Could you please provide more details or clarify what you meant?"
            )
            dispatcher.utter_message(
                text="Please reply with the number or name of the movie you'd like to select (e.g., 1 for Zodiac, 2 for Constantine)."
            )
            dispatcher.utter_message(
                text="I'm here to help with any inquiries about our Athena bot service! 😊"
            )
            return [UserUtteranceReverted()]

class ActionFetchShowtimes(Action):
    def name(self):
        return "action_fetch_showtimes"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        # Sample showtimes for demonstration purposes
        showtime_mappings = {
            "Zodiac": ["10:00 AM", "01:00 PM", "04:00 PM", "07:00 PM"],
            "Constantine": ["11:00 AM", "02:00 PM", "05:00 PM", "08:00 PM"],
        }

        selected_movie = tracker.get_slot("movie")

        if not selected_movie or selected_movie not in showtime_mappings:
            dispatcher.utter_message(
                text="I couldn't find showtimes for the selected movie. Could you please confirm the movie first?"
            )
            return []

        # Fetch showtimes for the selected movie
        showtimes = showtime_mappings[selected_movie]
        showtimes_list = "\n".join(
            [f"{i+1}: {time}" for i, time in enumerate(showtimes)])

        # Send showtimes to the user
        dispatcher.utter_message(
            text=f"Here are the available showtimes for {selected_movie}:\n{showtimes_list}\nPlease reply with the number corresponding to your preferred showtime."
        )

        return []



class ActionSetShowtime(Action):
    def name(self) -> Text:
        return "action_set_showtime"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        # Sample showtimes for demonstration purposes
        showtime_mappings = {
            "Zodiac": ["10:00 AM", "01:00 PM", "04:00 PM", "07:00 PM"],
            "Constantine": ["11:00 AM", "02:00 PM", "05:00 PM", "08:00 PM"],
        }

        selected_movie = tracker.get_slot("movie")
        user_input = tracker.latest_message.get("text", "")

        if not selected_movie or selected_movie not in showtime_mappings:
            dispatcher.utter_message(
                text="I couldn't find the movie you selected. Could you confirm the movie first?"
            )
            return [SlotSet("showtime", None)]

        showtimes = showtime_mappings[selected_movie]

        # First, try to extract a numeric choice
        match_numeric = re.search(r"\b(\d+)\b", user_input)
        if match_numeric:
            choice = int(match_numeric.group(1)) - 1  # Convert to zero-based index
            if 0 <= choice < len(showtimes):
                selected_showtime = showtimes[choice]
                dispatcher.utter_message(
                    text=f"You have selected {selected_showtime} for {selected_movie}."
                )
                dispatcher.utter_message(
                    text="Please select the location to watch the movie."
                )
                dispatcher.utter_message(response="utter_ask_location")
                return [SlotSet("showtime", selected_showtime)]

        # Next, try to extract a time-based input
        match_time = re.search(r"\b(\d{1,2}:\d{2} (?:AM|PM))\b", user_input, re.IGNORECASE)
        if match_time:
            requested_time = match_time.group(1).strip().upper()
            if requested_time in showtimes:
                dispatcher.utter_message(
                    text=f"You have selected {requested_time} for {selected_movie}."
                )
                dispatcher.utter_message(
                    text="Please select the location to watch the movie."
                )
                dispatcher.utter_message(response="utter_ask_location")
                return [SlotSet("showtime", requested_time)]
            else:
                dispatcher.utter_message(
                    text=f"Sorry, {requested_time} is not available for {selected_movie}. Please choose from the available times: {', '.join(showtimes)}."
                )
                return [SlotSet("showtime", None)]

        # If no valid input is found, prompt the user again
        dispatcher.utter_message(
            text=f"I didn't understand your choice. Please select a valid number or showtime from the list: {', '.join(showtimes)}."
        )
        return [SlotSet("showtime", None)]


class ActionSetLocation(Action):
    def name(self):
        return "action_set_location"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        # Extract location from user input
        user_input = tracker.latest_message.get("text")
        location = user_input
        dispatcher.utter_message(
            text=f"You have selected {location} as the location to watch the movie")
        dispatcher.utter_message(response="action_fetch_cinemas")
        return [SlotSet("location", location)]

class ActionFetchCinemas(Action):
    def name(self):
        return "action_fetch_cinemas"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        user_location = next(
            tracker.get_latest_entity_values("location"), None)

        # Cinema mappings
        cinema_mappings = {
            "hong kong": {
                "1": "Grand Ocean (Ocean Centre)",
                "2": "The Sky (Olympian City)",
                "3": "StagE (Tuen Mun Town Plaza Phase 1)"
            },
            "singapore": {
                "1": "Golden Mile Tower",
                "2": "Cathay Cineleisure Orchard"
            },
            "malaysia": {
                "1": "GSC Mid Valley",
                "2": "GSC Pavilion KL",
                "3": "GSC Paradigm Mall"
            }
        }

        # Acronym mappings
        acronym_mappings = {
            "hk": "hong kong",
            "sg": "singapore",
            "my": "malaysia"
        }

        # Check if location is provided
        if not user_location:
            dispatcher.utter_message(
                text="I couldn't detect your location. Could you please tell me where you are?")
            return []

        # Normalize the location input
        location = user_location.lower()
        # Map acronyms to full names
        location = acronym_mappings.get(location, location)

        if location not in cinema_mappings:
            dispatcher.utter_message(text="Sorry, I didn't understand that.")
            dispatcher.utter_message(
                text="It seems you tried to say something else.")
            dispatcher.utter_message(
                text="Could you please provide more details or clarify what you meant?")
            dispatcher.utter_message(
                text="I'm here to help with any inquiries about our Athena bot service! 😊")

            return []

        # Fetch cinemas for the user's location
        cinemas = cinema_mappings[location]
        cinema_list = "\n".join(
            [f"{key}: {name}" for key, name in cinemas.items()])

        dispatcher.utter_message(
            text=f"Here are the cinemas available in {location.title()}:\n{cinema_list}\nPlease reply with the number corresponding to your choice."
        )

        # Save location in the slot
        return [SlotSet("location", location)]


class ActionSetCinema(Action):
    def name(self):
        return "action_set_cinema"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        import re
        # Extract the user input
        user_input = tracker.latest_message.get("text", "").lower()
        user_location = tracker.get_slot("location")

        # Cinema mappings
        cinema_mappings = {
            "hong kong": {
                "1": "Grand Ocean (Ocean Centre)",
                "2": "The Sky (Olympian City)",
                "3": "StagE (Tuen Mun Town Plaza Phase 1)"
            },
            "singapore": {
                "1": "Golden Mile Tower",
                "2": "Cathay Cineleisure Orchard"
            },
            "malaysia": {
                "1": "GSC Mid Valley",
                "2": "GSC Pavilion KL",
                "3": "GSC Paradigm Mall"
            }
        }

        # Validate the user's location
        if not user_location or user_location.lower() not in cinema_mappings:
            dispatcher.utter_message(
                text="I couldn't determine your location. Please provide a valid location.")
            return [SlotSet("cinema", None)]

        # Fetch cinemas for the user's location
        location_cinemas = cinema_mappings[user_location.lower()]

        # First, try to match a number in the input
        match = re.search(r"\b(\d+)\b", user_input)  # Matches any number
        if match:
            cinema_number = match.group(1)  # Extract the matched number
            selected_cinema = location_cinemas.get(cinema_number)

            if selected_cinema:
                # If valid cinema number is found
                dispatcher.utter_message(
                    text=f"You have selected {selected_cinema} in {user_location.title()}. Enjoy your time at the cinema!")
                return [SlotSet("cinema", selected_cinema), FollowupAction("action_ask_seats_type")]

        # If no number is matched, search for a cinema name
        for cinema_number, cinema_name in location_cinemas.items():
            if cinema_name.lower() in user_input:
                # If cinema name matches, confirm and set the slot
                dispatcher.utter_message(
                    text=f"You have selected {cinema_name} in {user_location.title()}. Enjoy your time at the cinema!")
                return [SlotSet("cinema", cinema_name), FollowupAction("action_ask_seats_type")]

        # If neither a number nor a cinema name is matched
        cinema_list = "\n".join(
            [f"{key}: {name}" for key, name in location_cinemas.items()])
        dispatcher.utter_message(
            text=f"Sorry, I couldn't understand that. Please reply with the number or name corresponding to your choice:\n{cinema_list}"
        )
        return [SlotSet("cinema", None)]


class ActionAskSeatsType(Action):
    def name(self):
        return "action_ask_seats_type"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        # Retrieve user's location
        user_location = tracker.get_slot("location")

        # Location-based seat pricing with currencies
        seat_prices_by_location = {
            "malaysia": {
                "prices": {"VIP": 50, "Standard": 30, "Couple": 80},
                "currency": "MYR"
            },
            "hong kong": {
                "prices": {"VIP": 150, "Standard": 100, "Couple": 250},
                "currency": "HKD"
            },
            "singapore": {
                "prices": {"VIP": 100, "Standard": 70, "Couple": 200},
                "currency": "SGD"
            }
        }

        # Validate user location
        if not user_location or user_location.lower() not in seat_prices_by_location:
            dispatcher.utter_message(
                text="I couldn't determine your location for pricing. Please confirm your location first."
            )
            return []

        # Get seat prices and currency for the user's location
        location_data = seat_prices_by_location[user_location.lower()]
        location_seat_prices = location_data["prices"]
        currency = location_data["currency"]

        # Constructing the message with prices
        seat_options_with_prices = "\n".join(
            [f"- {seat_type}: {price} {currency}" for seat_type, price in location_seat_prices.items()]
        )

        dispatcher.utter_message(
            text="What type of seats would you like to book? Here are the options:"
        )
        dispatcher.utter_message(text=seat_options_with_prices)

        return []



class ActionSetSeatsType(Action):
    def name(self):
        return "action_set_seats_type"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        selected_seats_type = next(
            tracker.get_latest_entity_values("seat_type"), None)
        
        # Retrieve user's location
        user_location = tracker.get_slot("location")

        # Location-based seat pricing with currencies
        seat_prices_by_location = {
            "malaysia": {
                "prices": {"vip": 50, "standard": 30, "couple": 80},
                "currency": "MYR"
            },
            "hong kong": {
                "prices": {"vip": 150, "standard": 100, "couple": 250},
                "currency": "HKD"
            },
            "singapore": {
                "prices": {"vip": 100, "standard": 70, "couple": 200},
                "currency": "SGD"
            }
        }

        # Validate user location
        if not user_location or user_location.lower() not in seat_prices_by_location:
            dispatcher.utter_message(
                text="I couldn't determine your location for pricing. Please confirm your location first."
            )
            return [SlotSet("seat_type", None)]

        # Get seat prices and currency for the user's location
        location_data = seat_prices_by_location[user_location.lower()]
        location_seat_prices = location_data["prices"]
        currency = location_data["currency"]

        valid_seat_types = location_seat_prices.keys()

        # Validate seat type
        if selected_seats_type and selected_seats_type.lower() in valid_seat_types:
            price = location_seat_prices[selected_seats_type.lower()]
            dispatcher.utter_message(
                text=f"You have selected the {selected_seats_type.capitalize()} section in {user_location.title()}. The price per seat is {price} {currency}."
            )
            return [SlotSet("seat_type", selected_seats_type), FollowupAction("action_ask_seat_number")]
        else:
            # Handle invalid or unrecognized seat type
            dispatcher.utter_message(text="Sorry, I didn't understand that.")
            dispatcher.utter_message(
                text="It seems you tried to say something else.")
            dispatcher.utter_message(
                text="Please specify the type of seats you want (VIP, Standard, Couple).")
            return [UserUtteranceReverted()]

        return []




class ActionAskSeatNumber(Action):
    def name(self):
        return "action_ask_seat_number"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        image_url = "https://www.edrawsoft.com/templates/images/cinema-seating-plan.png"

        dispatcher.utter_message(image=image_url)
        dispatcher.utter_message(text="Please enter the seat number of the seat you would like to reserve.")

        return []


class ActionSetSeatsNumber(Action):
    def name(self):
        return "action_set_seats_number"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        selected_seats = next(
            tracker.get_latest_entity_values("seat_number"), None)

        if selected_seats and selected_seats.isdigit():
            dispatcher.utter_message(
                text=f"You have selected seat number {selected_seats}.")
            return [SlotSet("seat_number", selected_seats), FollowupAction("action_ask_confirmation")]
        else:
            dispatcher.utter_message(text="Sorry, I didn't understand that.")
            dispatcher.utter_message(
                text="It seems you tried to say something else.")
            dispatcher.utter_message(
                text=" Please specify the number of seats you want.")
            dispatcher.utter_message(
                text="Could you please provide more details or clarify what you meant?")
            dispatcher.utter_message(
                text="I'm here to help with any inquiries about our Athena bot service! 😊")
            return [UserUtteranceReverted()]

        return []


class ActionAskConfirmation(Action):
    def name(self):
        return "action_ask_confirmation"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        messages = [
            "Please confirm your booking by replying with 'Confirm' or 'Cancel'.",
            "Are you sure you want to proceed with the booking?",
            "Please confirm your booking details."
        ]

        for message in messages:
            dispatcher.utter_message(text=message)

        return []
    
class ActionSetConfirmation(Action):
    def name(self):
        return "action_set_confirmation"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        confirmation = tracker.latest_message.get("text", "").lower()

        if "confirm" in confirmation:
            dispatcher.utter_message(text="Your booking is confirmed!")
            return [SlotSet("decide", "confirm"), FollowupAction("action_ask_payment_option")]
        elif "cancel" in confirmation:
            dispatcher.utter_message(text="Your booking has been canceled. Feel free to ask if you need anything else!")
        else:
            dispatcher.utter_message(text="Sorry, I didn't understand that.")
            dispatcher.utter_message(text="Please confirm your booking by replying with 'Confirm' or 'Cancel'.")

        return []


class ActionConfirmBooking(Action):
    def name(self):
        return "action_confirm_booking"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        # Fetching all the slots
        selected_cinema = tracker.get_slot("cinema")
        selected_movie = tracker.get_slot("movie")
        selected_seats = tracker.get_slot("seat_number")
        selected_seats_type = tracker.get_slot("seat_type")

        confirmation = tracker.latest_message.get("text", "").lower()

        # If all required slots are filled, ask for confirmation
        if selected_movie and selected_cinema and selected_seats and selected_seats_type:
            if "confirm" in confirmation:
                # If user confirmed the booking, proceed with confirmation message
                dispatcher.utter_message(
                    text=f"Your booking is confirmed!\nMovie: {selected_movie}\nCinema: {selected_cinema}\nSeats: {selected_seats} ({selected_seats_type})."
                )
                return [FollowupAction("action_ask_payment_option")]
            elif "cancel" in confirmation:
                # If user canceled, provide a cancellation message
                dispatcher.utter_message(
                    text="Your booking has been canceled. Feel free to ask if you need anything else!")
            else:
                # If user's confirmation intent is unclear, ask for confirmation again
                dispatcher.utter_message(
                    text="Sorry, I didn't understand that.")
                dispatcher.utter_message(
                    text="Please confirm your booking by replying with 'Confirm' or 'Cancel'.")
        else:
            # If booking details are incomplete, ask user to retry
            dispatcher.utter_message(
                text="Sorry, some booking details are missing. Please try again.")

        return []


class ActionAskPaymentOptions(Action):
    def name(self):
        return "action_ask_payment_option"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        messages = [
            "Now that you have confirmed your ticket.",
            "Let us get started on the payment process.",
            "Please decide between the different options of payment.",
            "The payment options we provide are:",
            "Master, Visa & Paypal"
        ]
        for message in messages:
            dispatcher.utter_message(text=message)

        return []


class ActionSetPaymentOption(Action):
    def name(self):
        return "action_set_payment_option"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        payment_option = next(
            tracker.get_latest_entity_values("payment_option"), None)

        valid_payment_options = [
            "credit card", "debit card", "paypal", "apple pay", "mastercard", "visa", "master"]
        if payment_option and payment_option.lower() in valid_payment_options:
            dispatcher.utter_message(
                text=f"You have selected {payment_option} as your payment option.")
            dispatcher.utter_message(response="utter_payment_link")
            return [SlotSet("payment_option", payment_option), FollowupAction("action_booking_confirmed")]
        else:
            dispatcher.utter_message(text="Sorry, I didn't understand that.")
            dispatcher.utter_message(
                text="It seems you tried to say something else.")
            dispatcher.utter_message(
                text="Please specify a valid payment option (e.g., Credit Card, PayPal).")
            dispatcher.utter_message(
                text="Could you please provide more details or clarify what you meant?")
            dispatcher.utter_message(
                text="I'm here to help with any inquiries about our Athena bot service! 😊")
            return [UserUtteranceReverted()]

        return []


class ActionBookingConfirmed(Action):
    def name(self):
        return "action_booking_confirmed"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        dispatcher.utter_message(
            text="Your booking has been confirmed. Enjoy the movie!")
        return []
