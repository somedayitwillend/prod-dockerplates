import requests, json, config

def handle_response(data):
	f = open('data.html', mode="r", encoding="utf-8")
	html = f.read()
	f.close()
	response = requests.get('https://raider.io/api/v1/mythic-plus/season-cutoffs?season=season-df-3&region=eu')
	responseJson = json.loads(response.text)
	cutoff01 = responseJson['cutoffs']['p999']['all']['quantileMinValue']
	cutoff1 = responseJson['cutoffs']['p990']['all']['quantileMinValue']
	percentPerRio = (cutoff01 - cutoff1) / 9
	response = requests.get('https://raider.io/api/v1/characters/profile?region=eu&realm=Ragnaros&name=' + data + '&fields=mythic_plus_best_runs%2Cmythic_plus_alternate_runs')
	responseJson = json.loads(response.text)

	html = html.replace('PICS', config.ROOT_PATH + config.PICS_PATH)
	html = html.replace('FACTION', responseJson['faction'])
	html = html.replace('PLAYER.NAME', responseJson['name'])
	html = html.replace('PLAYER.AVATAR', responseJson['thumbnail_url'])
	score = 0
	for dungeon in responseJson['mythic_plus_best_runs']:
		type = 'TYRA' if 'Tyrannical' in str(dungeon['affixes']) else 'FORTI'
		html = html.replace(type + '.' + dungeon['short_name'], str(dungeon['mythic_level']))
		score = score + (dungeon['score'] * 1.5)
	
	for dungeon in responseJson['mythic_plus_alternate_runs']:
		type = 'TYRA' if 'Tyrannical' in str(dungeon['affixes']) else 'FORTI'
		html = html.replace(type + '.' + dungeon['short_name'], str(dungeon['mythic_level']))
		score = score + (dungeon['score'] * 0.5)
	
	html = html.replace('PLAYER.PERCENT', str(round((((cutoff01 - score) / percentPerRio) + 1) / 10, 2)))
	html = html.replace('PLAYER.SCORE', str(round(score, 1)))
	return {
     	'html': html,
		'rio': score
	}
