# SGRS
Steam Game Recommendation System

Dataset - https://www.kaggle.com/datasets/fronkongames/steam-games-dataset 


V1 - 
Current Backend Features:
user selects 3 games
-> program takes those threee games averages the vectors
- (the vector uses nlp of the tags, categories, and genres mainly -> along with some other values)
-> runs the avg_vector through a similarity matrix 
-> finds the 3 games that are most similar to it

Current UI Features:
- box for typing in games
- Filter/Search box under it to select games
- Selecting games shows the image of the game to allow user to confirm its the right game
- once they select 3 games, there is a button to get recommendations
- shows 3 recommended games and their similarity scores
- sort by price, user can select a range for the price they want


V2 - Changes
- Let the user select 1 or 2 games instead of just 3
- let the user decide how many games they want recommended to them.


Features to add:
- let the user select games they already have or dont want to play - saves a file to their computer to remember it for next time (allows them to edit it)



Computational issues
- Can't use full 90k songs and use the tfidf matrix
- had to use subset of games (decided to use games with achievements to recommend)

