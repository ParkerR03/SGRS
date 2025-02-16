import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.sparse import hstack
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity
import joblib

full_data = pd.read_csv('Data/Recommendation_allGames.csv')
rec_data = pd.read_csv('Data/Recommendation_WithAchievements.csv')
scaler = joblib.load('Stuff/scaler.pkl')            # price and days since reference .5 weight
scaler1 = joblib.load('Stuff/scaler1.pkl')          # wilson score .7 weight
vectorizer = joblib.load('Stuff/vectorizer.pkl')    # combined info .8 weight
weighted_features = joblib.load('Stuff/weighted_features.pkl')





def preprocess_user_input(user_games, full_data = full_data, vectorizer = vectorizer, scaler = scaler, scaler1 = scaler1):
    '''
    Takes a list of user-selected games (The AppID of the games) and retrieves their features from the fulldata,
    preprocesses the data and returns the averaged feature vector representation
    '''
    
    user_feature_vectors = []
    
    for game in user_games:
        # Check if game exists in full_data
        game_data = full_data[full_data['AppID'] == int(game)]
        if game_data.empty:
            print(f"Game ID {game} not found in dataset")
            continue
            
        combined_info = game_data['combined_info'].values[0]
        price = game_data['Price'].values[0]
        wilson_score = game_data['wilson_score'].values[0]
        days_since_release = game_data['dayssincereference'].values[0]
        
        combined_info_vector = vectorizer.transform([combined_info])
        
        numeric_features = np.array([[price, days_since_release]])
        numeric_features1 = np.array([[wilson_score]])
        
        numeric_features_scaled = scaler.transform(numeric_features)
        numeric_features1_scaled = scaler1.transform(numeric_features1)
        
        combined_vector = hstack([combined_info_vector, numeric_features_scaled, numeric_features1_scaled])
        
        combined_vector = combined_vector.toarray()
        
        user_feature_vectors.append(combined_vector)
    
    if not user_feature_vectors:
        raise ValueError("No valid games found to process")
        
    user_feature_vectors_avg = np.mean(user_feature_vectors, axis = 0)
    
    return user_feature_vectors_avg



# Have to update this to make it so it only recommends games that are not in the user's list and only those ones.
def get_recommendations(user_games, n = 5, data = rec_data, weighted_features = weighted_features):
    '''
    Takes the averaged feature vector representation of the user-selected games and returns the top n (default = 5) recommendations
    from the rec_data dataset
    '''
    # Get the average feature vector from full_data games
    try:
        user_feature_vectors_avg = preprocess_user_input(user_games)
    except Exception as e:
        print(f"Error preprocessing user games: {e}")
        return [], []

    # Calculate similarity with games in rec_data
    similarity_scores = cosine_similarity(user_feature_vectors_avg.reshape(1, -1), weighted_features)
    similarity_scores_flat = similarity_scores.flatten()
    
    # Get indices of user's games in rec_data (if they exist)
    user_game_indices = data[data['AppID'].isin(user_games)].index
    
    # Set similarity scores of user's games to -1 to exclude them
    similarity_scores_flat[user_game_indices] = -1
    
    # Get top n recommendations
    top_indices = similarity_scores_flat.argsort()[::-1]  # Sort all indices by similarity score
    top_indices = [i for i in top_indices if i not in user_game_indices][:n]  # Exclude user games and pick top n

    if not top_indices:
        raise ValueError("No recommendations found")

    return top_indices, similarity_scores_flat[top_indices]



def check_game(game):
    '''
    game is a string that is the name of a game
    
    output:
    Outputs True or False if the game is in the dataset
    '''
    
    try:
        app_id = int(game)
        if not full_data[full_data['AppID'] == app_id].empty:
            return True
    except ValueError:
        pass
    
    
    game = game.lower()
    matching_games = full_data[full_data['Name'].str.lower() == game]
    
    if matching_games.empty:
        print('Game not found in the dataset.')
        return False  # Game name not found
    elif matching_games.shape[0] > 1:
        print('Multiple games with this name found. Please use the AppID to specify.')
        return False  # Multiple games with the same name
    else:
        return True  # Unique game name found



def get_game_id(game):
    '''
    input: game name or id
    
    output:
    Outputs the id of the games
    '''
    
    # if its an id or game name, return the id
    
    try:
        app_id = int(game)
        if not full_data[full_data['AppID'] == app_id].empty:
            return app_id
    except ValueError:
        game = game.lower()
        matching_game = full_data[full_data['Name'].str.lower() == game]
        return matching_game['AppID'].values[0]


    
def get_game_index(list_of_ids):
    '''
    Input: list of game ids
    
    Output: returns the index of the games in the dataset rec_data
    '''

    game_indices = []
    
    for game in list_of_ids:
        game_indices.append(rec_data[rec_data['AppID'] == game].index[0])
        
    return game_indices
