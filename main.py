#!/usr/bin/env python
#
import webapp2, os, urllib2
import json, logging
import jinja2, urllib

JINJA_ENVIRONMENT = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

def pretty(obj):
    return json.dumps(obj, sort_keys=True, indent=2)

def safeGet(url):
    try:
        return urllib2.urlopen(url)
    except urllib2.URLError as e:
        if hasattr(e, "code"):
            logging.error("The server couldn't fulfill the request.")
            logging.error("Error code: ", e.code)
        elif hasattr(e, 'reason'):
            logging.error("We failed to reach a server")
            logging.error("Reason: ", e.reason)
        return None


# Keys for APIs
import keys

# Function to get Google Civic API Call based on Address
def civicREST(address,
               baseurl = 'https://www.googleapis.com/civicinfo/v2/representatives',
               api_key = keys.civic_key,
               params={},
               levels = 'country',
                ):
    params['address'] = address
    params['key'] = api_key
    params['levels'] = levels
    url = baseurl + "?" + urllib.urlencode(params)
    getdata = safeGet(url)
    funcdata = json.load(getdata)
    return funcdata

# Calls the Member List of Propublica to get Names and member IDS
def memIdREST(congress = "senate"):
    url = "https://api.propublica.org/congress/v1/116/%s/members.json"%(congress)
    request = urllib2.Request(url, headers={"X-API-Key": keys.congress_key})
    getdata = safeGet(request)
    funcdata = json.load(getdata)
    return funcdata

memberiddict = {}

# Makes a Dictionary with member names as key and IDs as values
def putMeminDict(congress):
    allmemberinfo = memIdREST(congress)
    for eachmeminfo in allmemberinfo["results"][0]["members"]:
        memfname = eachmeminfo["first_name"]
        memlname = eachmeminfo["last_name"]
        memposition = eachmeminfo["short_title"]
        memfull = memposition + " " + memfname + " " + memlname
        memid = eachmeminfo["id"]
        memberiddict[memfull] = memid

putMeminDict("senate")
putMeminDict("house")

def getPic(address):
    neededpics = []
    # Calling the Civic Rest Function with a provided Address for Pictures
    polpics = civicREST(address)
    for eachpic in polpics["officials"][2:5]:
        if "photoUrl" in eachpic:
            picURL = eachpic["photoUrl"]
        else:
            picURL = "https://upload.wikimedia.org/wikipedia/en/b/b1/Portrait_placeholder.png"
        neededpics.append(picURL)
    return neededpics

def getCivicPols(address):
    neededids = []
    needpols = []
    # Calling the Civic Rest Function with a provided Address for to find the 3 Representatives
    fullpoldet = civicREST(address)
    #Creating a list of all of their Senators and House Reps
    for eachsen in fullpoldet["officials"][2:4]:
        name = eachsen["name"]
        name = fixSenName(name)
        needpols.append("Sen. " + name)
    if len(fullpoldet["officials"]) == 5:
        name = fullpoldet["officials"][4]["name"]
        if (len(name.split()) > 2):
            name = name.split()[0] + " " + name.split()[-1]
        needpols.append("Rep. " + name)

    # Getting the Member IDs of the 3 Politicians using the memberiddict dictionary
    for eachrep in needpols:
        neededids.append(memberiddict[eachrep])
    return neededids

# Function to call the information on specific politicians
def memInfo(memberId):
    url = "https://api.propublica.org/congress/v1/members/%s.json" %(memberId)
    request = urllib2.Request(url, headers={"X-API-Key": keys.congress_key})
    getdata = safeGet(request)
    funcdata = json.load(getdata)
    return funcdata

def getPolInfo(neededids, address):
    pol_count = 0
    for allreps in neededids:
        #Call Information on the specific Rep and saves certain data to a dictionary
        eachinfo = memInfo(allreps)
        pol_count += 1
        name = eachinfo["results"][0]["roles"][0]["short_title"] + " " + eachinfo["results"][0]["first_name"] + " " + \
               eachinfo["results"][0]["last_name"]
        role = eachinfo["results"][0]["roles"][0]["committees"]
        fullcom = []
        for eachcom in role:
            info = eachcom["title"] + ", " + eachcom["name"]
            fullcom.append(info)
        url = eachinfo["results"][0]["url"]
        party = eachinfo["results"][0]["current_party"]
        twitter = eachinfo["results"][0]["twitter_account"]
        facebook = eachinfo["results"][0]["facebook_account"]
        youtube = eachinfo["results"][0]["youtube_account"]
        cosponsor = eachinfo["results"][0]["roles"][0]["bills_cosponsored"]
        sponsor = eachinfo["results"][0]["roles"][0]["bills_sponsored"]
        contactform = eachinfo["results"][0]["roles"][0]["contact_form"]
        nextelec = eachinfo["results"][0]["roles"][0]["next_election"]
        phone = eachinfo["results"][0]["roles"][0]["phone"]
        office = eachinfo["results"][0]["roles"][0]["office"]
        totalvotes = eachinfo["results"][0]["roles"][0]["total_votes"]
        partyvotes = eachinfo["results"][0]["roles"][0]["votes_with_party_pct"]
        chamber = eachinfo["results"][0]["roles"][0]["chamber"]
        title = eachinfo["results"][0]["roles"][0]["title"]
        polpics = getPic(address)
        pic = polpics[pol_count - 1]
        if eachinfo["results"][0]["roles"][0]["title"] == "Representative":
            district = eachinfo["results"][0]["roles"][0]["state"] + "-" + eachinfo["results"][0]["roles"][0]["district"]
        if pol_count == 1:
            pol_1 = {"name": name, "role": role, "comms": fullcom, "url": url, "party": party, "twitter": twitter,
                     "facebook": facebook, "youtube": youtube, "cosponsor": cosponsor, "sponsor": sponsor, "contact": contactform,
                     "next_elec": nextelec, "phone": phone, "office": office, "totalvotes": totalvotes, "partyvotes": partyvotes,
                     "chamber": chamber, "title": title, "pic": pic}
        elif pol_count == 2:
            pol_2 = {"name": name, "role": role, "comms": fullcom, "url": url, "party": party, "twitter": twitter,
                     "facebook": facebook, "youtube": youtube, "cosponsor": cosponsor, "sponsor": sponsor, "contact": contactform,
                     "next_elec": nextelec, "phone": phone, "office": office, "totalvotes": totalvotes,
                     "partyvotes": partyvotes, "chamber": chamber, "title": title, "pic": pic}
        else:
            pol_3 = {"name": name, "role": role, "comms": fullcom, "url": url, "party": party, "twitter": twitter,
                     "facebook": facebook, "youtube": youtube, "cosponsor": cosponsor, "sponsor": sponsor,
                     "contact": contactform, "next_elec": nextelec, "phone": phone, "office": office, "totalvotes": totalvotes,
                     "partyvotes": partyvotes, "district": district, "chamber": chamber, "title": title, "pic": pic}
    #List of the 3 politicians' information dictionaries
    pols = [pol_1, pol_2, pol_3]

    # Dictionary of Items needed for the template
    neededvalues = {"title": "Your Federal Representatives", "pols": pols}
    return neededvalues

class MainHandler(webapp2.RequestHandler):
    def genpage(self):
        # Landing Page
        landingvalues = {"info": "Address"}
        landtemp = JINJA_ENVIRONMENT.get_template('landingpage.html')
        self.response.write(landtemp.render(landingvalues))
    def get(self):
        #Calling the Landing Page first
        self.genpage()
    def post(self):
        #Taking Address Imput and generating the 3 politicians Info using Jinja template
        address = self.request.get('address')
        reps = getCivicPols(address)
        neededvalues = getPolInfo(reps, address)
        neededvalues["address"] = address
        template = JINJA_ENVIRONMENT.get_template('finalprojecttemplate.html')
        self.response.write(template.render(neededvalues))


application = webapp2.WSGIApplication([('/', MainHandler)], debug=True)



#Fix Some Senators Name to match Civic with ProPublica:
def fixSenName(Senator):
    name = Senator
    mismatch = {"Richard C. Shelby": "Richard Shelby", "Kamala D. Harris": "Kamala Harris",
                "Michael F. Bennet": "Michael Bennet", "Thomas R. Carper": "Thomas Carper",
                "Christopher A. Coons": "Christopher Coons", "Mazie K. Hirono": "Mazie Hirono",
                "Mike Crapo": "Michael Crapo", "Jim E. Risch": "Jim Risch", "Richard J. Durbin": "Richard Durbin",
                "Chuck Grassley": "Charles Grassley", "Angus S. King Jr.": "Angus King",
                "Susan M. Collins": "Susan Collins", "Benjamin L. Cardin": "Benjamin Cardin",
                "Edward J. Markey": "Edward Markey", "Gary C. Peters": "Gary Peters", "Roger F. Wicker": "Roger Wicker",
                "Josh Hawley": "Joshua Hawley", "Margaret Wood Hassan": "Margaret Hassan",
                "Cory A. Booker": "Cory Booker", "Charles E. Schumer": "Charles Schumer",
                "Kirsten E. Gillibrand": "Kirsten Gillibrand", "James M. Inhofe": "James Inhofe",
                "Robert P. Casey Jr.":  "Bob Casey", "Patrick J. Toomey": "Patrick Toomey",
                "Bernie Sanders": "Bernard Sanders", "Patrick J. Leahy": "Patrick Leahy",
                "Mark R. Warner": "Mark Warner", "Shelley Moore Capito": "Shelley Capito",
                "Joe Manchin III": "Joe Manchin", "Michael B. Enzi": "Michael Enzi"}
    if name in mismatch:
        name = mismatch[name]
    return name
