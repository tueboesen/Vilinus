# Vilinus
Warhammer campaign (realtime graph theory at work)


## Thoughts

Lav overtagelses mekanik (En sector kræver x points at overtage, hver army kan overtage med x points pr s), 

Når en hær ankommer til en sector så sker følgende:
	Is there an enemy army?: 
		Is there a current battle?:
			Hæren har nu mulighed for at joine kampen eller forsøge at passere kampen. ?? Eller autojoiner man så kampen?
		Else:
			Begge hære får oplyst den andens hærs default adfærd og har nu mulighed for at ændre deres egen adfærd (de har x sekunder til at ændre den):
				Flygt, fight, afvent
			Hvis en eller begge hære vælger at flygte, så vil den eller begge hærene flygte i den retning de kom fra.
			Hvis en eller begge hære har valgt fight så starter en kamp.
			Hvis begge hære har valgt afvent så har vi et standoff og en eller flere af hærene kan bevæge sig videre i andre retninger end dem de kom fra.		
	Else:
		Is the army ending in this sector?:
			Start controlling the sector if not already owned
		Else:
			Move the army onward
			

Supplies? how do we keep track of that? (I suggest that each sector have it as a characteristic, and when a sector changes control it is checked)
VP is awarded every tick for each sector controlled:
Furthermore VP is awarded as event triggers when a battle is completed.
Finally VP is awarded at the end of the campaign for controlled sectors.
VP is kept secret.



Team characteristics:
	Credits
	VP (victory points)
	Armies
	Teleports
	Backstabbers (Yes/No)
	

Army/Player characteristics:
	Relics:
	Sector cards:
	Faction
	Location
	Army composition / battle points: (What is visible to enemies? Approx battle strength? or full information?)
	battle ready: (True,False)
	destroyed: (True, False)

	Move speed
	takeover speed (how long it takes to control a sector for this army) (Do multiple armies add their speed or do they not stack?)
	
Player choices:
	Move
	Rearm 100, base, base+, full
	Transfer relic 

Captain choices:
	Teleport player1, player2
	Alliance Team


Alliances are not official until both team captains have used the command alliance on the other team.

Alliances are broken with the command.
	alliance None
	
	By default alliances are broken gracefully, but there is the optional keyword: backstab
	alliance None, backstab
	
	Gracefully, with a warning period of x minutes, where all armies leave the allies terretory and are away from their terretory before the period expire.
	Backstab, no warning period, armies become hostile immediately. A team will be known as backstabbers (for the remainder of the campaign or just for x hours?), and a penalty might be applied? 
	
