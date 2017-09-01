from PIL import Image, ImageEnhance, ImageFilter

import praw
import shutil
import requests
import pytesseract as ocr
import webbrowser
import random
import re

class bot():    

    def __init__(self, **kwargs):

        #place your reddit api secret, client id, username and password on seperate lines in validation.txt in this directory
        validation = self.loadCredentials()
        print(validation)
        self.secret = validation[0]
        self.clientId = validation[1]
        self.username = validation[2]
        self.password = validation[3]

        self.image_fname = "img"
        self.COMPLETED_IMAGE_ID_FILE = "visitedImages.txt"

        self.subreddit = "surrealmemes"
        self.NEEDS_APPROVAL = True

        self.preText = [ "**^^I ^^sense ^^letters:**", "**^^let ^^me ^^help ^^you ^^READ:**",]

        #need at least 10 chars per line of response text
        self.responseMinLineLength = 10

    def loadCredentials(self):
        ret = []
        with open("validation.txt", 'r') as file:
            for line in file:
                ret.append(line.rstrip())
        return ret

    def submissionFilter(self, submission):
        #only look for imgur links or direct hosted images
        if ("imgur.com" not in submission.url and "i.redd.it" not in submission.url):
            return False

        #we dont want imgur albums either
        if ("/a/" in submission.url):
            return False

        #also only take images that are linked directly so we can download them
        if (".jpg" not in submission.url and ".png" not in submission.url):
            return False

        #iterate through the filter file and see if it contains sumbission.id, if so we have already processed this image
        with open(self.COMPLETED_IMAGE_ID_FILE, "r") as file:
            for line in file:
                if submission.id in line.replace("\n",""):
                    #print("already worked on " + line)
                    return False               

        return True

    def recordNewSubmission(self, submissionId):
        with open(self.COMPLETED_IMAGE_ID_FILE, "a") as file:
            file.write(submissionId + "\n")

    def approveMessage(self, message):
        canReturn = False
        answer = False

        yes = [ 'yes', 'y', 'yea', 'yep', 'ye', ]
        no = [ 'no', 'n', 'nope', '', ]

        while True:
            msg = input(message + " Y/N: ").lower()
            if msg in yes:
                return True
            elif msg in no:
                return False
            else:
                print("please enter Y or N")

        return answer

    #prepare the text for submission at /r/surrealmemes, pretty much randomly applies combining characters to words ("zalgo" text)
    def surrealifyText(self, text):
        chanceLineIsZalgofied = 0.4
        changeWordIsAngery = 0.1
        responseMinLineLength = 10

        alphabet = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z']

        #downward going diacritics
        dd = ['̖',' ̗',' ̘',' ̙',' ̜',' ̝',' ̞',' ̟',' ̠',' ̤',' ̥',' ̦',' ̩',' ̪',' ̫',' ̬',' ̭',' ̮',' ̯',' ̰',' ̱',' ̲',' ̳',' ̹',' ̺',' ̻',' ̼',' ͅ',' ͇',' ͈',' ͉',' ͍',' ͎',' ͓',' ͔',' ͕',' ͖',' ͙',' ͚',' ',]
        #upward diacritics
        du = [' ̍',' ̎',' ̄',' ̅',' ̿',' ̑',' ̆',' ̐',' ͒',' ͗',' ͑',' ̇',' ̈',' ̊',' ͂',' ̓',' ̈́',' ͊',' ͋',' ͌',' ̃',' ̂',' ̌',' ͐',' ́',' ̋',' ̏',' ̒',' ̽',' ̉',' ͣ',' ͤ',' ͥ',' ͦ',' ͧ',' ͨ',' ͩ',' ͪ',' ͫ',' ͬ',' ͭ',' ͮ',' ͯ',' ̾',' ͛',' ͆',' ̚',]
        #build the alterations - zalgo and [text](/a) for shaking angery text
        dm = [' ̕',' ̛',' ̀',' ́',' ͘',' ̡',' ̢',' ̧',' ̨',' ̴',' ̵',' ̶',' ͜',' ͝',' ͞',' ͟',' ͠',' ͢',' ̸',' ̷',' ͡',' ҉','_',]
        

        #get each line of text
        lines = text.split("\n\n") #something like [pretext multiple words, text multi words line 1, text multi words line 2, etc... , post text]
        newLines = []

        #print(lines)
        #input("press enter to continue")

        ##we need to first merge some lines that are too short with a space
        #newnewLines = []
        #i = 0
        #maxI = len(lines)
        #while i < maxI:

        ##lines = newnewLines        

        numLines = len(lines)
        numWords = 0
        numLetters = 0

        #iterate through the lines
        for line in lines: # line = 'pretext multiple words' etc... goal: create newLine = 
            zalgofy = False
            if random.uniform(0,1) <= chanceLineIsZalgofied:
                zalgofy = True

            #get each word, decompose it into a list of letters, zalgofy and then recompose the words and lines individually... just watch
            words = line.split(' ') #something like [pretext, multiple, words,]
            newWords = []
            numWords = numWords + len(words)
            for word in words: # 'pretext' etc...
                #get the letters list
                letters = list(word) #['p','r','e',...]
                #print(letters)
                newWord = ''
                newLetters = letters

                numLetters = numLetters + len(letters)

                #zalgofy if we need to, then angery it if we need to
                if zalgofy:
                    newLetters = []
                    
                    #for each letter, add some diacritics in all directions
                    for letter in letters: #'p', etc...
                        a = letter #create a dummy letter

                        #skip this letter we can't add a diacritic to it
                        if not a.isalpha():
                            newLetters.append(a)
                            continue

                        num = random.randint(1,3)
                        #add the diacritics going up
                        for i in range(num):                            
                            d = du[random.randrange(0, len(du))]
                            a = a + d

                        num = random.randint(1,3)
                        #add the diacritics going down
                        for i in range(num):                            
                            d = dd[random.randrange(0, len(dd))]
                            a = a + d

                        num = random.randint(0,2)
                        #add the diacritics in the middle
                        for i in range(num):                            
                            d = dm[random.randrange(0, len(dm))]
                            a = a + d
                        
                        a = a.replace(" ","") #remove any spaces, this also gives it the zalgo text look
                        #print('accented a letter: ' + a)
                        newLetters.append(a)
                        
                newWord = ''.join(newLetters)
                if random.uniform(0,1) <= changeWordIsAngery:
                    if random.uniform(0,1) < 0.5:
                        newWord = "[" + newWord + "](/a)"
                    else:
                        newWord = "[" + newWord + "](/angery)"

                newWords.append(newWord)              

            newLines.append(' '.join(newWords))

        #recompose it back into a reddit comment and print some data
        text = "\n\n".join(newLines)
        #print(text)
        #input("press enter to continue")
        #print("Data from submission:")
        #print("Line count: " + str(numLines))
        #print("Word count: " + str(numWords))
        #print("Letter count: " + str(numLetters))
        return text

    #processes an image for OCR, fpath is assumed to be an image type file
    def processImage(self, fpath):
        image = Image.open(fpath)
        
        image = image.convert("L")
        image = image.filter(ImageFilter.GaussianBlur())
        #image = image.convert("1")
        
        image.save(fpath)
        return image

    def runBot(self):
        #get a Reddit instance
        reddit = praw.Reddit(client_id=self.clientId,
                        client_secret=self.secret,
                        password=self.password,
                        user_agent='python:ocr_bot:v0.1 (by /u/ocr_bot)',
                        username=self.username)

        print("Loaded ocr_bot...")
        print("Browsing posts from /r/" + self.subreddit)

        #deauthorize the reddit instance until just before we want to post
        reddit.read_only = True

        #get the /r/all subreddit
        all = reddit.subreddit(self.subreddit)

        while True:
            try:
                #loop through new posts
                for submission in all.hot():

                    if not self.submissionFilter(submission):
                        continue

                    print("Processing submission: " + submission.id)
                    #openInBrowser = self.approveMessage("Open in browser?")
                    #if (openInBrowser):
                    #webbrowser.open_new_tab(submission.shortlink)

                    #if (self.approveMessage("Skip this one?")):
                    #    if self.approveMessage("Add to skip list?"):
                    #        self.recordNewSubmission(submission.id)
                    #    continue

                    #get the pics extension so we can open the correct type of file
                    ext = submission.url[-4:]  
                    fpath = self.image_fname + ext

                    #download the image and copy it to a file
                    response = requests.get(submission.url, stream=True)
                    with open(fpath, "wb") as img_file:
                        shutil.copyfileobj(response.raw, img_file)           

                    #remove this data
                    del response

                    image = self.processImage(fpath)
                    text = ocr.image_to_string(image)

                    #automatically skip this one if there's no enough text, else ask for confirmation
                    if len(text.replace(" ", "")) == 0:
                        print("skipping " + submission.id + ", no text here")
                        self.recordNewSubmission(submission.id)
                        continue

            
                    #so newlines are actually newlines in the reddit comment
                    text = text.replace("\n", "\n\n")            
                    text = self.surrealifyText(text)
                    fulltext = self.surrealifyText(self.preText[random.randrange(0, len(self.preText))]) + "\n\n&nbsp;\n\n" + text + "\n\n&nbsp;\n\n^^^^created^^by^^some^^guy ^^^^^^| ^^^^^^[feedback](https://www.reddit.com/message/compose/?to=ocr_bot)"

                    if self.approveMessage("Found some text! Open page and compare with OCR?"):
                        webbrowser.open_new_tab(submission.shortlink)
                        print("\nFull Post:\n")
                        print(fulltext)

                    #try to post
                    try:
                        #check for approval
                        if self.NEEDS_APPROVAL:
                            if self.approveMessage("Approve above post?"):
                                #reauthorize the bot to post
                                reddit.read_only = False
                                submission.reply(fulltext)
                                print("submission approved")
                                #append the submission id to the file so we never work on it again
                                self.recordNewSubmission(submission.id)
                            else:
                                print("submission denied")
                                addToSkip = self.approveMessage("Add to skip list?")
                                if addToSkip:
                                    self.recordNewSubmission(submission.id)

                    except praw.exceptions.PRAWException:
                        print("There was an error posting...")
                        reddit.read_only = True
                        break

                    reddit.read_only = True

                    goAgain = self.approveMessage("Go again?")
                    if not goAgain:
                        print("exiting")
                        return None
            except praw.exceptions.PRAWException:
                if not self.approveMessage("There was an error, try again?"):
                    break
            except prawcore.exceptions.ResponseException:
                if not self.approveMessage("There was an error, try again?"):
                    break
    
def fixFiles():
    with open('diacritics_up.txt', 'r') as file:
        lines = file.read().splitlines()
        newlines = []
        regex = re.compile(r'\/\*(.*?)\*\/') #remove some stuff, this selects all of the unicode characters surrounded by space
        for line in lines:
            print(line)
            for match in re.findall(regex, line):
                print(match)
                newlines.append(match.replace(' ',''))

        print(newlines)
        if (len(newlines) > 0):
            print(type(newlines[0]))


if __name__ == "__main__": 
    a = bot()
    a.runBot()