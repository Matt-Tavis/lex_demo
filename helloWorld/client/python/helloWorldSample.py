from babyLex import LexSession
from microphone import Microphone
import signal
import pyaudio
import boto3
import wave
import time
from array import array

WW_ENABLED = False
INTERRUPTED = False

try:
	import snowboydecoder
	WW_ENABLED = True
except ImportError:
	WW_ENABLED = False

p = pyaudio.PyAudio()

lex_session = LexSession("TestBot", "$LATEST", "mtavis")
slowStream = p.open(format=p.get_format_from_width(width=2), channels=1, rate=16000, output=True)

m = Microphone()

# prep audio sounds
micOpenWav = wave.open("resources/avs_small_system_state_active_start.wav", 'rb')
fastStream = p.open(format=micOpenWav.getsampwidth(), channels=micOpenWav.getnchannels(), rate=micOpenWav.getframerate(), output=True)
micOpenWavAudio = micOpenWav.readframes(micOpenWav.getnframes())
micOpenWav.close()
micDoneWav = wave.open("resources/avs_small_system_state_user_speech_confirmed.wav", 'rb')
micDoneWavAudio = micDoneWav.readframes(micDoneWav.getnframes())
micDoneWav.close()


if WW_ENABLED:
	detector = snowboydecoder.HotwordDetector("resources/snowboy.umdl", sensitivity=0.5)

def signal_handler(signal, frame):
	global INTERRUPTED
	INTERRUPTED = True

def interrupt_callback():
	global INTERRUPTED
	return INTERRUPTED


signal.signal(signal.SIGINT, signal_handler)

def talk_to_lex():
	global lex_session
	while 1:
		#stream.write(audioInputBuffer)

		# real-time record input
		audioBuffer = array('h')

		fastStream.write(micOpenWavAudio)
		sample_width, snd_data = m.record(audioBuffer, echo=False)
		fastStream.write(micDoneWavAudio)

		resp = lex_session.content(bytes(snd_data), "audio/l16; rate=16000; channels=1", "audio/pcm")

		print(resp.headers)

		slowStream.write(resp.content)
		dialogState = resp.headers['x-amz-lex-dialog-state']

		if (dialogState == 'Fulfilled' or
			dialogState == 'ReadyForFulfillment' or
			dialogState == 'Failed'):
			break


# This is text input sample
#resp = lex_session.content("Where is Randall", "text/plain; charset=utf-8", "audio/pcm")

# This is audio content sample
# inputWav = wave.open("C:/data/amazon/alexa/lex/samples/helloWorld/SayHelloToMatt.wav", 'rb')

# inputFrames = inputWav.getnframes()
# audioInputBuffer = inputWav.readframes(inputFrames)




while 1:

	# determine if WW_ENABLED
	if not WW_ENABLED:
		input("Tap Enter to talk to Lex...")
		talk_to_lex()
	else:
		# drop in loop for Snowboy Detect
		print("Listening for my name...")
		detector.start(detected_callback=talk_to_lex, interrupt_check=interrupt_callback, sleep_time=0.3)


fastStream.stop_stream()
fastStream.close()
slowStream.stop_stream()
slowStream.close()