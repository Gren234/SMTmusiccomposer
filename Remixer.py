import os
import music21
import numpy as np
from music21 import converter, pitch, interval, note, chord
from music21 import stream
import tensorflow as tf
#Function for sorting midi files based on end user choice
def search(listOfFiles,parameter,mode):
    output = []
    for i in listOfFiles:
        if ".mid" in i:
            output.append(i)
    output2 = []
    for i in output:
        if mode == 1:
            if parameter in i:
                output2.append(i)
        else:
            if not parameter in i:
                output2.append(i)
    return output2 
battleOrNo = input("Would you like to create an output of only battle themes? (Y/N) ")
battleOrNo = battleOrNo.upper()

#Prompts User to select Y or N and prevents them from selecting anything else to keep the program from crashing
#Cannot have both types of songs in the same list because they are completely different in nature
while 1==1:
    if battleOrNo == "Y" or battleOrNo == "N":
        print ("Removing battle themes from input queue")
        break
    else:
        battleOrNo = input("Im sorry, you can only answer with Y or N ")
save_dir = "."

#Gets all the midi files in the directory and puts them in a list 
songListTemp = os.listdir(save_dir)
songList = []
if battleOrNo == "Y":
    songList = search(songListTemp,"Battle",1)
else:
    songList = search(songListTemp,"Battle",2)
songListParsed=[]

#Parses the midi 
for i in songList:
    score = converter.parse(i)
    songListParsed.append(score)

#creates empty lists for future use
songChords = [[] for _ in songListParsed]
songDurations = [[] for _ in songListParsed]
songKeys = []

#Creating lists of Chords, Durations and Keys which are data that the program needs to continue
for i,song in enumerate(songListParsed):
    songKeys.append(str(song.analyze('key')))
    for element in song:
        if isinstance(element, note.Note):
            songChords[i].append(element.pitch)
            songDurations[i].append(element.duration.quarterLength)
        elif isinstance(element, chord.Chord):
            songChords[i].append('.'.join(str(n) for n in element.pitches))
            songDurations[i].append(element.duration.quarterLength)

#Map unique chords to integers
uniqueChords = np.unique([i for s in songChords for i in s])
chordToInt = dict(zip(uniqueChords, list(range(0, len(uniqueChords)))))
#Map unique durations to integers
uniqueDurations = np.unique([i for s in songDurations for i in s])

#If there are no unique chords or durations then uniqueDurations and uniqueChords are set to the same value as songDurations and songChords respectively
if len(uniqueChords) == 0:
    uniqueChords = songChords
if len(uniqueDurations) == 0:
    uniqueDurations = songDurations
#Define sequence length
sequenceLength = 32

#Define empty arrays for train data
trainChords = []
trainDurations = []

#Construct training sequences for chords and durations
for s in range(len(songChords)):
    chordList = [chordToInt[c] for c in songChords[s]]
    durationList = [durationToInt[d] for d in songDurations[s]]
    for i in range(len(chordList) - sequenceLength):
        trainChords.append(chordList[i:i+sequenceLength])
        trainDurations.append(durationList[i:i+sequenceLength])
#Convert one-hot encoding and swap chord and sequence dimensions
trainChords = tf.keras.utils.to_categorical(trainChords).transpose(0,2,1)

#convert data to numpy array of type float
trainChords = np.array([trainChords],np.float)

# Flatten sequence of chords into single dimension 
trainChordsFlat = trainChords.reshape(nSamples.inputDim)

# Define encoder input shape
encoderInput = tf.keras.layers.Input(shape = (inputDim))

# Define decoder input shape
latent = tf.keras.layers.Input(shape = (latentDim))

# Define dense encoding layer connecting input to latent vector
encoded = tf.keras.layers.Dense(latentDim, activation = 'tanh')(encoderInput)

# Define dense decoding layer connecting latent vector to output
decoded = tf.keras.layers.Dense(inputDim, activation = 'sigmoid')(latent)

# Define the encoder and decoder models
encoder = tf.keras.Model(encoderInput, encoded)
decoder = tf.keras.Model(latent, decoded)

# Define autoencoder model
autoencoder = tf.keras.Model(encoderInput, decoder(encoded))

# Compile autoencoder model
autoencoder.compile(loss = 'binary_crossentropy', learning_rate = 0.01,optimizer='rmsprop')

# Train autoencoder
autoencoder.fit(trainChordsFlat, trainCChordsFlat, epochs = 500)

# Generate chords from randomly generated latent vector
generatedChords = decoder(np.random.normal(size=(1,latentDim))).numpy().reshape(nChords, sequenceLength).argmax(0)

#set location to save generated music
generated_dir = './MyTunes'

generatedStream = stream.Stream()