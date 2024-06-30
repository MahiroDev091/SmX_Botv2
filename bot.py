import requests
from fbchat import Client
from fbchat.models import *
import re
from concurrent.futures import ThreadPoolExecutor
import os
import threading
import json
import sys
import time
import subprocess
from datetime import datetime, timedelta

try:
    with open('config.json') as f:
        configuration = json.load(f)
except FileNotFoundError:
    sys.exit("SORRY, AN ERROR ENCOUNTERED WHILE FINDING 'CONFIG.JSON'.")
except json.decoder.JSONDecodeError:
    sys.exit("SORRY, AN ERROR ENCOUNTERED WHILE READING THE JSON FILE.")

repeat = '4'
proccesses = []

class MessBot(Client):
    def load_cooldown_data(self, filename='cooldown.json'):
        try:
            with open(filename, 'r') as file:
                data = json.load(file)
        except FileNotFoundError:
            data = {}
        return data 

    def save_cooldown_data(self, data, filename='cooldown.json'):
        with open(filename, 'w') as file:
            json.dump(data, file, indent=4)

    def format_timedelta(self, td):
        minutes, seconds = divmod(int(td.total_seconds()), 60)
        return f"{minutes} minutes and {seconds} seconds"

    def get_cooldown_remaining(self, user_id, cooldown_data):
        with open('config.json') as f:
        	cooldown_exist = json.load(f)['COOLDOWN']
        	cooldown_period = 30 * 60 if not cooldown_exist else int(cooldown_exist) * 60
        if user_id in cooldown_data:
            last_used = datetime.strptime(cooldown_data[user_id], '%Y-%m-%d %H:%M:%S')
            expiry_time = last_used + timedelta(seconds=cooldown_period)
            remaining_time = expiry_time - datetime.now()
            if remaining_time.total_seconds() > 0:
                return remaining_time
        return None

    def update_cooldown(self, user_id, cooldown_data, reset):
        if reset:
        	if user_id in cooldown_data:
        		del cooldown_data[user_id]
        else:
        	cooldown_data[user_id] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def sendmessage(self, author_id, thread_id, thread_type, reply, mid):
        if author_id != self.uid:
        	self.send(Message(text=reply, reply_to_id=mid), thread_id=thread_id, thread_type=thread_type)

    def mobile_add(self, value, file_name='config.json'):
    	with open(file_name, 'r') as file:
    		data = json.load(file)
    		data['PROTECTED_MOBILE_NUMBER'].append(str(value))
    	with open(file_name, 'w') as file:
    		json.dump(data, file, indent=4)
    
    def mobile_exists(self, value, file_name='config.json'):
    	with open(file_name, 'r') as file:
    		return value in json.load(file)['PROTECTED_MOBILE_NUMBER']
    def mobile_delete(self, value, file_name='config.json'):
    	with open(file_name, 'r') as file:
    		data = json.load(file)
    	if value in data['PROTECTED_MOBILE_NUMBER']:
    		data['PROTECTED_MOBILE_NUMBER'].remove(str(value))
    		with open(file_name, 'w') as file:
    			json.dump(data, file, indent=4)
    		return True
    	else:
    		return False
    	
    def onMessage(self, mid=None, author_id=None, message_object=None, thread_id=None, thread_type=ThreadType.USER, **kwargs):
        try:
            global proccesses
            cooldown_data = self.load_cooldown_data()
            with open('config.json') as f:
                configuration = json.load(f)
            msg = message_object.text
            prefix = str(configuration['PREFIX'])
            if msg.startswith("prefix"):
                reply = f"🚀 BOT PREFIX: {prefix}"
                self.sendmessage(author_id, thread_id, thread_type, reply, mid)
                
            if msg.startswith(f"{prefix}setting"):
            	if author_id in configuration['ADMIN_IDS']:
            		selection = msg[len(prefix) + 8:]
            		if not selection:
            			reply = """⚙️ SmX_Botv2 Setting:
- setprefix <prefix>: change prefix
- remove <phonenumber>: remove phone number from the blocklist
- setcooldown <cooldown>: change cooldown time for users"""
            			self.sendmessage(author_id, thread_id, thread_type, reply, mid)
            		elif selection.startswith('setprefix'):
            			if len(selection.split()) != 2:
            				reply = "❌ Please enter your new bot prefix!"
            				self.sendmessage(author_id, thread_id, thread_type, reply, mid)
            			else:
            				if selection.split()[1] not in ['#', '<', '>', '=', '-', '+', '*', '/', '^', '%', '$', '!', '?', '_', '&', ':', ';', '|'] or selection.split()[1] == prefix:
            					reply = "❌ The prefix must not be the same as the one the bot is using and must use only symbols."
            					self.sendmessage(author_id, thread_id, thread_type, reply, mid)
            				else:
            					with open("config.json", "r") as jsonFile:
            						data = json.load(jsonFile)
            					data['PREFIX'] = str(selection.split()[1])
            					
            					with open("config.json", "w") as jsonFile:
            						json.dump(data, jsonFile, indent=3)
            					reply = "✅ Prefix was successfully changed!"
            					self.sendmessage(author_id, thread_id, thread_type, reply, mid)
            		elif selection.startswith('remove'):
            			if len(selection.split()) != 2:
            				reply = '❌ Please enter the phone number you want to remove from the blocklist!'
            				self.sendmessage(author_id, thread_id, thread_type, reply, mid)
            			else:
            				if not selection.split()[1].startswith("09") or len(selection.split()[1]) != 11:
            					reply = '❌ Please enter your valid phone number; the number must start with 09 and have a length of 11 digits.'
            					self.sendmessage(author_id, thread_id, thread_type, reply, mid)
            				else:
            					if self.mobile_delete(str(selection.split()[1])):
            						reply = "✅ This phone number has now been removed from the blocklist!"
            						self.sendmessage(author_id, thread_id, thread_type, reply, mid)
            					else:
            						reply = "❌ This phone number is not on the blocklist!"
            						self.sendmessage(author_id, thread_id, thread_type, reply, mid)
            		elif selection.startswith('setcooldown'):
            			if len(selection.split()) != 2:
            				reply = '❌ Please enter your new cooldown time!'
            				self.sendmessage(author_id, thread_id, thread_type, reply, mid)
            			else:
            				if selection.split()[1] == configuration['COOLDOWN']:
            					reply = "❌ The cooldown time must not be the same as the one the bot is using."
            					self.sendmessage(author_id, thread_id, thread_type, reply, mid)
            				else:
            					if selection.split()[1].isnumeric():
            						with open("config.json", "r") as jsonFile:
            							data = json.load(jsonFile)
            						data['COOLDOWN'] = str(selection.split()[1])
            						with open("config.json", "w") as jsonFile:
            							json.dump(data, jsonFile, indent=3)
            						reply = f"✅ Cooldown time was successfully changed to {selection.split()[1]}minutes!"
            						self.sendmessage(author_id, thread_id, thread_type, reply, mid)
            					else:
            						reply = '❌ Please enter the valid cooldown time!'
            						self.sendmessage(author_id, thread_id, thread_type, reply, mid)
            		else:
            			reply = "❌ Command not found!"
            			self.sendmessage(author_id, thread_id, thread_type, reply, mid)
            	else:
            		reply = "❌ Only admin(s) can access this command!"
            		self.sendmessage(author_id, thread_id, thread_type, reply, mid)
            		
            if msg.startswith(f"{prefix}catfact"):
            	facts = requests.get('https://catfact.ninja/fact').json()['fact']
            	reply = f"😺 CATFACT:\n{facts}"
            	self.sendmessage(author_id, thread_id, thread_type, reply, mid)
            		
            if msg.startswith(f"{prefix}help"):
            	sender_name = self.fetchUserInfo(author_id)[author_id].name
            	reply = f"""@SmX_Botv2:
- {prefix}sms: <phonenumber>: send spam sms & call
- {prefix}gpt4: <question>: ask anything
- {prefix}catfact: get fact about cats
- {prefix}status: check the total count of requests
- {prefix}guard <phonenumber>: shield your number from spam
- {prefix}uid: get my facebook id
- {prefix}setting: change the configuration setup
"""
            	self.sendmessage(author_id, thread_id, thread_type, reply, mid)
            	reply = f"Hi {sender_name}, How may i help you?"
            	self.sendmessage(author_id, thread_id, thread_type, reply, mid)
            	
            if msg.startswith(f"{prefix}guard"):
            	mobile_number = msg[len(prefix) + 6:]
            	if not mobile_number:
            		reply = f"""🚧 This protection will work only on SmX_Botv1.
❌ FORMAT: {prefix}guard 090xxxxx415
            		"""
            		self.sendmessage(author_id, thread_id, thread_type, reply, mid)
            	else:
            		if not mobile_number.startswith("09") or len(mobile_number) != 11:
            					reply = '❌ PLEASE ENTER THE VALID PH NUMBER FORMAT!'
            					self.sendmessage(author_id, thread_id, thread_type, reply, mid)
            		else:
            						if self.mobile_exists(mobile_number):
            							reply = "❌ Your phone number is already protected!"
            							self.sendmessage(author_id, thread_id, thread_type, reply, mid)
            						else:
            							self.mobile_add(mobile_number)
            							reply = "✅ Your phone number are now protected, you can rest assured!"
            							self.sendmessage(author_id, thread_id, thread_type, reply, mid)     			
            if msg.startswith(f"{prefix}gpt4"):
            	question = msg[len(prefix) + 5:]
            	if question != '':
            		try:
            			sender_name = self.fetchUserInfo(author_id)[author_id].name
            			question = msg[len(prefix) + 6:]
            			response = requests.get(f'https://api.kenliejugarap.com/freegpt4o8k/?question={question}').json()['response']
            			reply = f"🤖 GPT4 ANSWER:\n{response}\n\n🗯 Question from: {sender_name}"
            			self.sendmessage(author_id, thread_id, thread_type, reply, mid)
            		except:
            			reply = f"❌ An error encountered while fetching the request."
            			self.sendmessage(author_id, thread_id, thread_type, reply, mid)
            	else:
            		reply = f"❌ FORMAT: {prefix}gpt4 <question>"
            		self.sendmessage(author_id, thread_id, thread_type, reply, mid)
            		
            if msg.startswith(f"{prefix}sms"):
                sender_name = self.fetchUserInfo(author_id)[author_id].name
                remaining_time = self.get_cooldown_remaining(author_id, cooldown_data)
                if remaining_time is not None:
                    reply = f"❌ Please wait for {self.format_timedelta(remaining_time)} before submitting again."
                    self.sendmessage(author_id, thread_id, thread_type, reply, mid)
                else:
                    number = msg[len(prefix) + 4:]
                    if not number.startswith('09') or len(number) != 11:
                        reply = f"""❌ ENTER THE VALID PH NUMBER!
Usage: {prefix}sms 09xxxxxxx15"""
                        self.sendmessage(author_id, thread_id, thread_type, reply, mid)
                    else:
                        is_secured = self.mobile_exists(number)
                        if is_secured:
                        	self.update_cooldown(author_id, cooldown_data, True)
                        	reply = "❌ This phone number is protected, and cannot be spam!"
                        	self.sendmessage(author_id, thread_id, thread_type, reply, mid)
                        else:
                            def start_process():
                                try:
                                	file_path = os.path.join(os.getcwd(), "sms.py")
                                	process = subprocess.Popen(["python", file_path, number, repeat])
                                except Exception as e:
                                	return e

                            start_spamming = threading.Thread(target=start_process)
                            start_spamming.start()
                            if start_spamming.is_alive():
                            	proccesses.append(number)
                            	self.update_cooldown(author_id, cooldown_data, False)
                            	self.save_cooldown_data(cooldown_data)
                            	reply = f"""
🚀 Attack Sent Successfully 🚀
User 🗯: {sender_name}
Target 📱: [ {number} ]
Repeats ⚔️: [ {repeat} ]
Country Code 🇵🇭: ( +63 )
Plan 💸: [ FREE ]
Owner 👑: Mahîro chan
"""
                            	self.sendmessage(author_id, thread_id, thread_type, reply, mid)
                            else:
                            	self.update_cooldown(author_id, cooldown_data, True)
                            	reply = "❌ An error occured while processing the request!"
                            	self.sendmessage(author_id, thread_id, thread_type, reply, mid)
                            
            if msg.startswith(f"{prefix}status"):
                if author_id in configuration['ADMIN_IDS']:
                	reply = f"✅ Total number of requests: {len(proccesses)}"
                	self.sendmessage(author_id, thread_id, thread_type, reply, mid)
                else:
                	reply = "❌ Only admin(s) can access this command!"
                	self.sendmessage(author_id, thread_id, thread_type, reply, mid)
                	
            if msg.startswith(f"{prefix}uid"):
                sender_name = self.fetchUserInfo(author_id)[author_id].name
                reply = f"Hi, {sender_name}\n𝚃𝙷𝙸𝚂 𝙸𝚂 𝚈𝙾𝚄𝚁 𝙸𝙳:\n{author_id}"
                self.sendmessage(author_id, thread_id, thread_type, reply, mid)
        except Exception as e:
            print(f"Error: {e}")
            
if __name__ == '__main__':
    try:
        converted_data = json.load(open('appstate.json', 'r'))
        session_cookies = {item["key"]: item["value"] for item in converted_data}
        bot = MessBot(' ', ' ', session_cookies=session_cookies, max_tries=1)
        print("LISTENING: {}".format(str(bot.isLoggedIn()).upper()))
        bot.listen()
    except Exception as e:
        sys.exit(f"FAILED TO CONNECT TO FACEBOOK SERVER: {e}")
