import re, subprocess, json
sites = {
 "Arizona":"arizonawildcats.com","Arizona State":"thesundevils.com","Baylor":"baylorbears.com",
 "BYU":"byucougars.com","Cincinnati":"gobearcats.com","Colorado":"cubuffs.com","Houston":"uhcougars.com",
 "Iowa State":"cyclones.com","Kansas":"kuathletics.com","Kansas State":"kstatesports.com",
 "Oklahoma State":"okstate.com","TCU":"gofrogs.com","Texas Tech":"texastech.com","UCF":"ucfknights.com",
 "Utah":"utahutes.com","West Virginia":"wvusports.com"}
out={}
for team,dom in sites.items():
    links=[]
    for path in ["sports/womens-soccer/schedule/2026","sports/womens-soccer/schedule"]:
        h=subprocess.run(["curl","-sL","-A","Mozilla/5.0","--max-time","45",f"https://{dom}/{path}"],capture_output=True,text=True).stdout
        links += re.findall(r'href="(/sports/womens-soccer/stats/\d{4}/[^"/]+/boxscore/\d+)"',h)
        links += re.findall(r'href="(/boxscore/\d+)"',h)
        links += re.findall(r'href="(/boxscore\.aspx\?id=\d+)"',h)
        if links: break
    seen=set(); u=[]
    for l in links:
        if l in seen: continue
        seen.add(l); u.append(l)
    out[team]={"dom":dom,"links":u}
    print(team,len(u))
json.dump(out,open('scheds2.json','w'),indent=1)
