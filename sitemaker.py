import requests
from bs4 import BeautifulSoup
import statistics
import csv
from datetime import datetime

class batsman:
    def __init__(self, player_info): #this takes info from our scraper and turns it into a python class
        
        #Player Info
        self.name = player_info[0]
        self.id_ = player_info[1]
        self.country = player_info[2]
        #the following line generates the Cricinfo URL based on the player ID
        self.player_runs_URL = f'http://stats.espncricinfo.com/ci/engine/player/{self.id_}.html?class=1;filter=advanced;orderby=runs;size=200;template=results;type=batting;view=innings'
        
        #Player stats
        self.runs = []
        self.not_outs = 0
        self.stdev = None
        self.average = None
        self._50s = 0
        self._100s = 0
        self.highscore = None
        self.reliability = None
    
    def run_formatter(self, score):
        score = str(score)
        score = score.strip('*') #removes pesky not-out notation which interferes with the code
        try:
            return int(score)
        except ValueError:
            pass #removes innings listed as DNB or TDNB
    
    def run_cleaner(self): #Removes runs listed as None (which will be caused by team no batting)
        self.runs = [run for run in self.runs if run is not None] #could probably tidy up my error handling instead but cba
    
    def add_runs(self):
        player_res = requests.get(self.player_runs_URL) #opens the players cricinfo page
        player_res.raise_for_status()
        player_soup = BeautifulSoup(player_res.text) #Reads all the HTML on the page
        player_data = player_soup.find_all('table')[3] #finds the table in the middle of the page
        for row in player_data.find_all('tr'): #Gets the rows
            try:
                runs_scored = row.find('td').text #runs is the first column
                if '*' in runs_scored:
                    self.not_outs += 1
                self.runs.append(self.run_formatter(runs_scored)) #copies the run into the runs dictionary
            except:
                pass
            
        self.run_cleaner()
        
    def __repr__(self):
        return self.name

def get_player_info(data_row):
    player = data_row.find_all('td')[0]
    player_name = player.a.text
    
    player_id = player.a['href'].strip('/ci/content/player/.html') #this removes all the bits from the href that aren't the number
    
    player_country = player.text.replace(player_name,'').replace('ICC','').replace('/','').strip(' ()') #yes i know I should use regex quit telling me
    return player_name, player_id, player_country

def fifties_and_hundreds(player):
    for runs in player.runs:
        if runs > 49:
            player._50s += 1
        if runs > 99:
            player._100s += 1

def sort_players(player):
    return sum(player.runs) # change this to be whatever you want to sort the players by

def main():
	
	#gets male test batsmen, change URL if you want to get different cricketers
	print("Getting players")
	top200_page = 'http://stats.espncricinfo.com/ci/engine/stats/index.html?class=1;filter=advanced;orderby=runs;size=200;template=results;type=batting'
	top200_data = requests.get(top200_page)
	
	#Gets list of players
	if top200_data.status_code == 200:
	    top200_soup = BeautifulSoup(top200_data.text)
	    tables = top200_soup.find_all('table')
	    rows = tables[2].find_all('tr')
	else: 
	    raise "connection to cricinfo gone wrong somewhere"

	#populates a list of batsmen
	print("creating list of batsmen & basic Data")
	top_200 = [batsman(get_player_info(row)) for row in rows[1:]]
	if len(top_200) != 200:
	    raise "You've not got 200 players for some reason, check scraper is working"

	#downloads the bating statistics for each of the batsmen in the list
	c = 1 
	print("Downloading Data for each batsman....")
	for player in top_200:
	    if c % 10 == 0:
	        print(c, 'Downloading',player.name ,'data.')
	    player.add_runs()
	    c += 1
	#makes timestamp
	now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")    

	#calculates all their statistics    
	for player in top_200:
	    player.stdev = statistics.stdev(player.runs)
	    player.average = sum(player.runs)/(len(player.runs)-player.not_outs)
	    player.highscore = max(player.runs)
	    fifties_and_hundreds(player)
	    player.reliability = player.average/player.stdev


	#Ranks them
	rankedPlayers = sorted(top_200, key=sort_players)

	#outputs all their statistics as a CSV file
	with open('top200_batsmen.csv', 'w', newline='') as csvfile:
	    print("Saving CSV")
	    csvwriter = csv.writer(csvfile)
	    csvwriter.writerow(['Name','Country','Runs','Average', 'Standard Deviation', 'Reliability', 'Dependableness','50s','100s','highscore','','Table Created',now])
	    for player in rankedPlayers:
	        csvwriter.writerow([player,player.country,sum(player.runs), round(player.average,2), round(player.stdev,2), round(player.reliability,4),round((player.average**2)/player.stdev,2), player._50s,player._100s,player.highscore])    

	#Creates the HTML version of the data table
	#Creates the table header        
	table = '''
	<table class=\"sortable\">
	\t<thead>
	\t\t<tr>
	\t\t\t<th>Name</th>
	\t\t\t<th>Country</th>
	\t\t\t<th>Runs</th>
	\t\t\t<th>Average</th>
	\t\t\t<th>Standard Deviation</th>
	\t\t\t<th>Reliability</th>
	\t\t\t<th>Dependableness</th>
	\t\t\t<th>50s</th>
	\t\t\t<th>100s</th>
	\t\t\t<th>Highscore</th>
	\t\t</tr>
	\t</thead>
	\t<tbody>
	'''
	
	#iterates through the players and adds a row for each player
	for player in rankedPlayers:
	        table += str(
	        '''
	        \t\t<tr>
	        \t\t\t<td>'''+str(player)+'''</td>
	        \t\t\t<td>'''+str(player.country)+'''</td>
	        \t\t\t<td>'''+str(sum(player.runs))+'''</td>
	        \t\t\t<td>'''+str(round(player.average,2))+'''</td>
	        \t\t\t<td>'''+str(round(player.stdev,2))+'''</td>
	        \t\t\t<td>'''+str(round(player.reliability,2))+'''</td>
	        \t\t\t<td>'''+str(round((player.average**2)/player.stdev,2))+'''</td>
	        \t\t\t<td>'''+str(player._50s)+'''</td>
	        \t\t\t<td>'''+str(player._100s)+'''</td>
	        \t\t\t<td>'''+str(player.highscore)+'''</td>
	        \t\t</tr>''')
	        
	table += '''
	\t</tbody>
	</table>'''

	#writes the webpage

	with open("template.html",'r') as template_file:
		template = template_file.read()

	print("saving webpage")
	output = template.replace("=== Add Table Here ===", table).replace("=== Add Timestampe Here ===", "Data downloaded: " + str(now))

	with open("index.html", "w") as output_file:
		output_file.write(output)


if __name__ == '__main__':
	main()
