from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.label import Label
from kivy.properties import BooleanProperty, ObjectProperty, ListProperty
from kivy.properties import StringProperty, NumericProperty
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.network.urlrequest import UrlRequest
from kivy.lang import Builder
from kivy.factory import Factory
import re
import datetime
import json

#For GPS
'''from plyer import gps
from kivy.clock import Clock, mainthread
from kivy.uix.popup import Popup'''

APPID = 'INSERT YOUR API KEY HERE'

class SelectableRecycleBoxLayout(FocusBehavior, LayoutSelectionBehavior,
                                 RecycleBoxLayout):
    ''' Adds selection and focus behaviour to the view. '''


class SelectableLabel(RecycleDataViewBehavior, Label):
    ''' Add selection support to the Label '''
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def refresh_view_attrs(self, rv, index, data):
        ''' Catch and handle the view changes '''
        self.index = index
        return super(SelectableLabel, self).refresh_view_attrs(
            rv, index, data)

    def on_touch_down(self, touch):
        ''' Add selection on touch down '''
        if super(SelectableLabel, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        ''' Respond to the selection of items in the view. '''
        self.selected = is_selected
        if is_selected:
            text_string = rv.data[index]['text']
            self.location = re.sub('\(|\)', '',text_string).rsplit(' ',1)
            print('Selected {}'.format(self.location))
            self.parent.parent.parent.parent.show_current_weather(self.location)#Fix This


class AddLocationForm(BoxLayout):
    search_input = ObjectProperty()
    search_results = ObjectProperty()

    def search_location(self):
        search_template = "http://api.openweathermap.org/data/2.5/" + "find?q={}&type=like&APPID={}"
        search_url = search_template.format(self.search_input.text, APPID)
        request = UrlRequest(search_url,self.found_location)

    def found_location(self, request, data):
        data = json.loads(data.decode()) if not isinstance(data, dict) else data
        cities = ["{} ({})".format(d['name'], d['sys']['country']) for d in data['list']]
        self.search_results.data = [{'text': str(x)} for x in cities]
        print(f"self.search_results.data={self.search_results.data}")

    #GPS
    '''def current_location(self):
        try:
            gps.configure(on_location=self.on_location)
            gps.start()
        except NotImplementedError:
            popup = Popup(title="GPS Error",content=Label(text="GPS support is not implemented on your platform")).open()
            Clock.schedule_once(lambda d: popup.dismiss(), 3)

    @mainthread
    def on_location(self, **kwargs):
        search_template = "http://api.openweathermap.org/data/2.5/" +
            "weather?lat={}&lon={}"
        search_url = search_template.format(kwargs['lat'], kwargs['lon'])
        data = requests.get(search_url).json()
        location = (data['sys']['country'], data['name'])
        WeatherApp.get_running_app().root.show_current_weather(location)'''


class CurrentWeather(BoxLayout):
    location = ListProperty(['New York', 'US'])
    conditions = StringProperty()
    temp = NumericProperty()
    temp_min = NumericProperty()
    temp_max = NumericProperty()
    conditions_image = StringProperty()
    temp_type = StringProperty()

    def update_weather(self):
        config = TestApp.get_running_app().config
        self.temp_type = config.getdefault('General','temp_type', 'metric').lower()
        weather_template = "http://api.openweathermap.org/data/2.5/" + "weather?q={},{}&units={}&APPID={}"
        weather_url = weather_template.format(*self.location,self.temp_type,APPID)
        request = UrlRequest(weather_url, self.weather_retrieved)
        
    def weather_retrieved(self, request, data):
        data = json.loads(data.decode()) if not isinstance(data, dict) else data
        self.conditions = data['weather'][0]['description']
        self.conditions_image = "http://openweathermap.org/img/w/{}.png".format(data['weather'][0]['icon'])
        self.temp = data['main']['temp']
        self.temp_min = data['main']['temp_min']
        self.temp_max = data['main']['temp_max']

class Forecast(BoxLayout):
    location = ListProperty(['New York', 'US'])
    forecast_container = ObjectProperty()

    def update_weather(self):
        config = TestApp.get_running_app().config
        temp_type = config.getdefault("General", "temp_type", "metric").lower()
        weather_template = "http://api.openweathermap.org/data/2.5/forecast" +"?q={},{}&units={}&cnt=10&APPID={}"
        weather_url = weather_template.format(
            self.location[0], 
            self.location[1], 
            temp_type,
            APPID)
        request = UrlRequest(weather_url, self.weather_retrieved)
            
    def weather_retrieved(self, request, data):
        data = json.loads(data.decode()) if not isinstance(data, dict) else data
        self.forecast_container.clear_widgets()
        for day in data['list']:
            label = Factory.ForecastLabel()
            label.date = datetime.datetime.fromtimestamp(day['dt']).strftime(
                "%a %b %d")

            label.conditions = day['weather'][0]['description']
            label.conditions_image = "http://openweathermap.org/img/w/{}.png".format(
                day['weather'][0]['icon'])
            label.temp_min = day['main']['temp_min']
            label.temp_max = day['main']['temp_max']
            self.forecast_container.add_widget(label)


class WeatherRoot(BoxLayout):

    current_weather = ObjectProperty()
    forecast = ObjectProperty()
    locations = ObjectProperty()

    def show_current_weather(self, location = None):
        self.clear_widgets()

        if self.current_weather is None:
           self.current_weather = CurrentWeather()
    
        if location is not None:
            self.current_weather.location = location

        self.current_weather.update_weather()
        self.add_widget(self.current_weather)

    def show_forecast(self, location=None):
        self.clear_widgets()

        if self.forecast is None:
            self.forecast = Factory.Forecast()

        if location is not None:
            self.forecast.location = location

        self.forecast.update_weather()
        self.add_widget(self.forecast)

    def show_add_location_form(self):
        self.clear_widgets()
        self.add_widget(AddLocationForm())


class TestApp(App):
    title = "Weather App"
    def build_config(self, config):
        config.setdefaults('General', {'temp_type': "Metric"})

    def build_settings(self, settings):
        settings.add_json_panel("Weather Settings", self.config, data="""
            [
                {"type": "options",
                    "title": "Temperature System",
                    "section": "General",
                    "key": "temp_type",
                    "options": ["Metric", "Imperial"]
                }
            ]"""
            )

    def on_config_change(self, config, section, key, value):
        if config is self.config and key == "temp_type":
            try:
                self.root.children[0].update_weather()
            except AttributeError:
                pass
            
    #GPS
    '''def on_pause(self):
        return True'''

    def build(self):
        return Builder.load_file("main.kv")


if __name__ == '__main__':
    TestApp().run()
