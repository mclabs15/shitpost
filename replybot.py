# coding=utf-8
from __future__ import print_function
from shitpostbot import *
import atexit
import multiprocessing
path = os.path.dirname(sys.argv[0])

def getUniques(l):
	nl = l[:]
	cl = l[:]
	for i in l:
		intimes = 0
		while i in cl:
			intimes += 1
			cl.remove(i)
		if intimes > 1:
			for j in xrange(intimes-1):
				nl.remove(i)
	return nl


class cSL(tweepy.StreamListener):
 
	def on_data(self, data):
		jdata = json.loads(data.strip())
		name = jdata.get('user', {}).get('screen_name', 'Name not found')
		displayname = jdata.get('user', {}).get('name', 'Name not found')
		selfname = api.me().screen_name
		cprint("Replying to tweet: ")
		cprint(format("{name} (@{handle})", name=displayname, handle=name))
		cprint(jdata.get('text'))
 
		retweeted = jdata.get('retweeted', False)
		from_self = jdata.get('user', {}).get('id',0) == api.me().id
		people = jdata.get('entities', {}).get('user_mentions', [])
		peoplenames = getUniques([i.get('screen_name') for i in people])
		if name in peoplenames:     peoplenames.remove(name)
		if selfname in peoplenames: peoplenames.remove(selfname)
		peoplenames.insert(0, name)
		names = " ".join([format("@{handle}", handle=i) for i in peoplenames if i])

		dot = "." if config.get('public') in jdata.get('text', '') else ""

		if isinstance(jdata.get('notags'), str):
			if jdata.get('notags') in jdata.get('text', ''):
				dot, names = "", ""
		elif isinstance(jdata.get('notags'), list):
			removedots = True
			for i in jdata.get('notags'):
				if i not in jdata.get('text', ''):
					removedots = False
			if removedots:
				dot, names = "", ""

		if jdata.get('text', '')[:2] != "RT" and not retweeted and not from_self:
			try:
				text = generate(debug=True)
				api.update_status(status=dot+names+" "+text, in_reply_to_status_id = jdata.get('id_str', ''))
				cprint(format("Sent tweet: {text}", text=dot+names+" "+text))
			except Exception, e:
				cprint(tbformat(e, "Error in sending tweet:"), color=bcolors.RED)
		print()
		return True
 
	def on_error(self, status):
		cprint("Error: "+str(status), color=bcolors.DARKRED)
		time.sleep(5)
		return True
 
def tweetStream():
	l = cSL()
	stream = tweepy.Stream(api.auth, l)

	while True:
		try:
			targets = []
			if isinstance(config.get("searchfor"), str):
				targets.append(config.get("searchfor"))
			elif isinstance(config.get("searchfor"), list):
				targets = config.get("searchfor")
			else:
				targets = ["gimme a shitpost", "gimme a public shitpost"]
			while not connected_to_internet():
				time.sleep(1)
			stream.filter(track=targets)
		except Exception, e:
			if isinstance(e, KeyboardInterrupt): 
				break
			cprint(tbformat(e, "Error in stream filter:"), color=bcolors.RED)
			print()

def cleanup():
	global replyThread, mainThread
	replyThread.terminate()
	mainThread.terminate()

def centralmain():
	global replyThread, mainThread
	atexit.register(cleanup)
	if not os.path.exists(os.path.join(path, "shitpostconfig.json")):
		json.dump({
			"time": 360,
			"notifytime": 60,
			"searchfor": ["gimme a shitpost", "gimme a public shitpost"],
			"public": "public",
			"notags": ["just", "do it"]
			}, open(os.path.join(path, "shitpostconfig.json"), "w"), indent=2, sort_keys=True)
	replyThread = multiprocessing.Process(target=tweetStream)
	mainThread = multiprocessing.Process(target=main)
	replyThread.start()
	mainThread.start()
	try:
		while True: time.sleep(0.001)
	except KeyboardInterrupt: cleanup()

if __name__ == "__main__": centralmain()