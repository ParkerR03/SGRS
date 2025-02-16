import tkinter as tk
from tkinter import ttk
import pandas as pd
from PIL import Image, ImageTk
import requests
from io import BytesIO
from recfunctions import get_recommendations, get_game_id, rec_data

# Load the games data
data = pd.read_csv('Data/Full_games.csv')

class GameSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Game Recommendation System")
        
        # Set window size
        self.root.geometry("600x1000")
        
        # Import recommendation functions and data
        self.get_recommendations = get_recommendations
        self.get_game_id = get_game_id
        self.rec_data = rec_data
        
        # Load the games data
        self.data = pd.read_csv('Data/Full_games.csv')
        self.selected_games = []
        
        # Create canvas with scrollbar
        self.canvas = tk.Canvas(root)
        self.scrollbar = ttk.Scrollbar(root, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        # Configure the canvas
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Pack the scrollbar and canvas
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # Create main frame inside scrollable frame with more padding
        self.main_frame = ttk.Frame(self.scrollable_frame)
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Add title/instructions with larger font and padding
        self.instructions = ttk.Label(
            self.main_frame, 
            text="Game Recommendation System\nPlease select 3 games you enjoy to receive recommendations",
            font=('Arial', 14),
            justify='center'
        )
        self.instructions.grid(row=0, column=0, columnspan=2, padx=20, pady=20)
        
        # Create main container frame
        self.left_frame = ttk.Frame(self.main_frame)
        self.left_frame.grid(row=1, column=0, padx=50, pady=10)
        
        # Configure column weight to center content
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)
        
        # Move search elements to left frame with more spacing
        self.search_var = tk.StringVar()
        self.search_var.trace_add('write', self.update_list)
        
        # Search section first
        self.search_label = ttk.Label(
            self.left_frame,
            text="Search for games:",
            font=('Arial', 11)
        )
        self.search_label.grid(row=0, column=0, padx=5, pady=(0, 5))
        
        self.search_entry = ttk.Entry(
            self.left_frame, 
            textvariable=self.search_var,
            width=60,
            font=('Arial', 10)
        )
        self.search_entry.grid(row=1, column=0, padx=5, pady=(0, 15))
        
        # Search image below search bar
        self.image_frame = ttk.Frame(self.left_frame)
        self.image_frame.grid(row=2, column=0, padx=10, pady=10)
        
        self.image_label = ttk.Label(self.image_frame)
        self.image_label.pack()
        
        # Search results section
        self.results_label = ttk.Label(
            self.left_frame,
            text="Search Results:",
            font=('Arial', 11)
        )
        self.results_label.grid(row=3, column=0, padx=5, pady=(0, 5))
        
        self.listbox = tk.Listbox(
            self.left_frame, 
            width=50, 
            height=10,
            font=('Arial', 10)
        )
        self.listbox.grid(row=4, column=0, padx=5, pady=(0, 20))
        
        # Selected games section
        self.selected_label = ttk.Label(
            self.left_frame, 
            text="Selected Games (0/3):",
            font=('Arial', 11)
        )
        self.selected_label.grid(row=5, column=0, padx=5, pady=(0, 5))
        
        self.selected_listbox = tk.Listbox(
            self.left_frame, 
            width=50, 
            height=3,
            font=('Arial', 10)
        )
        self.selected_listbox.grid(row=6, column=0, padx=5, pady=(0, 20))
        
        # Selected games images below selected games box
        self.selected_images_frame = ttk.Frame(self.left_frame)
        self.selected_images_frame.grid(row=7, column=0, padx=5, pady=5)
        
        # List to store selected game image labels with more spacing
        self.selected_image_labels = []
        for i in range(3):
            label = ttk.Label(self.selected_images_frame)
            label.grid(row=i, column=0, pady=10)
            self.selected_image_labels.append(label)
        
        # Store selected game photos
        self.selected_photos = []
        
        # Bind selection event
        self.listbox.bind('<Double-Button-1>', self.select_game)
        self.selected_listbox.bind('<Double-Button-1>', self.remove_game)
        
        # Initial population of the listbox
        self.update_list()
        
        # Modify listbox binding to also show image
        self.listbox.bind('<<ListboxSelect>>', self.show_game_image)
        
        # Recommendation button with larger font and padding
        self.recommend_button = ttk.Button(
            self.main_frame,
            text="Get Recommendations",
            command=self.show_recommendations,
            state='disabled'
        )
        self.recommend_button.grid(row=2, column=0, columnspan=2, pady=30)
        
        # Recommendations frame
        self.recommendations_frame = ttk.Frame(self.main_frame)
        self.recommendations_frame.grid(row=8, column=0, columnspan=2, padx=20, pady=20, sticky='nsew')
        
        # Configure the main_frame grid to center the recommendations
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        self.recommendations_label = ttk.Label(
            self.recommendations_frame, 
            text="Recommended Games:",
            font=('Arial', 11)
        )
        self.recommendations_label.pack()
        
        # Create frame for recommended games and their images
        self.recommended_games_frame = ttk.Frame(self.recommendations_frame)
        self.recommended_games_frame.pack(fill=tk.BOTH, expand=True)
        
        # List to store recommendation image labels
        self.recommendation_images = []
    
    def _on_mousewheel(self, event):
        """Handle mousewheel scrolling"""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def show_game_image(self, event):
        try:
            # Check if there's a valid selection
            if not self.listbox.curselection():
                return
                
            # Get selected game
            selection = self.listbox.get(self.listbox.curselection())
            game_id = selection.split("ID: ")[1].rstrip(")")
            
            # Get game's header image URL
            game_data = self.data[self.data['AppID'] == int(game_id)].iloc[0]
            image_url = game_data['Header image']
            
            # Fetch and display the image
            response = requests.get(image_url)
            image_data = BytesIO(response.content)
            image = Image.open(image_data)
            
            # Resize image to reasonable dimensions
            image = image.resize((300, 140), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage and keep a reference
            self.photo = ImageTk.PhotoImage(image)
            self.image_label.config(image=self.photo)
            
        except Exception as e:
            # Clear image if there's an error
            self.image_label.config(image='')
            print(f"Error loading image: {e}")
        
    def update_list(self, *args):
        search_term = self.search_var.get().lower()
        self.listbox.delete(0, tk.END)
        
        # Filter games based on search term
        if search_term:
            matches = self.data[self.data['Name'].str.lower().str.contains(search_term, na=False)]
            for _, game in matches.iterrows():
                if len(matches) > 100:  # Limit results to prevent lag
                    break
                self.listbox.insert(tk.END, f"{game['Name']} (ID: {game['AppID']})")
    
    def select_game(self, event):
        if len(self.selected_games) >= 3:
            return
        
        selection = self.listbox.get(self.listbox.curselection())
        if selection not in self.selected_games:
            self.selected_games.append(selection)
            self.update_selected_games_display()
    
    def remove_game(self, event):
        try:
            selection = self.selected_listbox.get(self.selected_listbox.curselection())
            self.selected_games.remove(selection)
            self.update_selected_games_display()
        except:
            pass
    
    def update_selected_games_display(self):
        self.selected_listbox.delete(0, tk.END)
        for i, game in enumerate(self.selected_games):
            self.selected_listbox.insert(tk.END, game)
            # Update image for this slot
            self.update_selected_game_image(i, game)
            
        # Clear remaining image slots
        for i in range(len(self.selected_games), 3):
            self.selected_image_labels[i].config(image='')
            
        self.selected_label.config(text=f"Selected Games ({len(self.selected_games)}/3):")
        
        if len(self.selected_games) == 3:
            self.recommend_button.config(state='normal')
        else:
            self.recommend_button.config(state='disabled')

    def update_selected_game_image(self, index, game):
        try:
            game_id = game.split("ID: ")[1].rstrip(")")
            game_data = self.data[self.data['AppID'] == int(game_id)].iloc[0]
            image_url = game_data['Header image']
            
            response = requests.get(image_url)
            image_data = BytesIO(response.content)
            image = Image.open(image_data)
            image = image.resize((300, 140), Image.Resampling.LANCZOS)
            
            # Keep reference to photo
            if len(self.selected_photos) <= index:
                self.selected_photos.append(None)
            self.selected_photos[index] = ImageTk.PhotoImage(image)
            
            self.selected_image_labels[index].config(image=self.selected_photos[index])
        except Exception as e:
            print(f"Error loading image: {e}")
            self.selected_image_labels[index].config(image='')

    def show_recommendations(self):
        # Clear previous recommendations
        for widget in self.recommended_games_frame.winfo_children():
            widget.destroy()
        self.recommendation_images = []
        
        try:
            # Get AppIDs of selected games
            game_ids = [int(game.split("ID: ")[1].rstrip(")")) for game in self.selected_games]
            
            if len(game_ids) != 3:
                raise ValueError(f"Need exactly 3 games for recommendations.")
            
            print(f"Processing recommendations for game IDs: {game_ids}")
            
            # Get recommendations using the existing function
            recommended_indices, similarity_scores = self.get_recommendations(game_ids, n=3)
            
            if not recommended_indices:
                raise ValueError("No recommendations found. Please try different games.")
            
            # Get recommended games data
            recommended_games = self.rec_data.iloc[recommended_indices]
            
            # Add a title for recommendations
            title_label = ttk.Label(
                self.recommended_games_frame,
                text="Recommended Games",
                font=('Arial', 12, 'bold'),
                justify='center'
            )
            title_label.pack(pady=(0, 20))
            
            # Create a frame to hold all recommendation cards
            cards_frame = ttk.Frame(self.recommended_games_frame)
            cards_frame.pack(expand=True, fill='both')
            
            # Configure grid weights to center the cards
            cards_frame.grid_columnconfigure(0, weight=1)
            cards_frame.grid_columnconfigure(1, weight=1)
            cards_frame.grid_columnconfigure(2, weight=1)
            
            # Display each recommended game
            for idx, (_, game) in enumerate(recommended_games.iterrows()):
                game_frame = ttk.Frame(cards_frame)
                game_frame.grid(row=0, column=idx, padx=20, pady=5)
                
                # Add game name and similarity score
                name_label = ttk.Label(
                    game_frame, 
                    text=f"{game['Name']}\nSimilarity: {similarity_scores[idx]:.2f}",
                    wraplength=300,
                    justify='center',
                    font=('Arial', 10)
                )
                name_label.pack(pady=(0, 10))
                
                # Add game image
                try:
                    header_image = self.data[self.data['AppID'] == game['AppID']]['Header image'].iloc[0]
                    
                    response = requests.get(header_image)
                    image_data = BytesIO(response.content)
                    image = Image.open(image_data)
                    image = image.resize((300, 140), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(image)
                    self.recommendation_images.append(photo)
                    
                    image_label = ttk.Label(game_frame, image=photo)
                    image_label.pack(pady=5)
                except Exception as e:
                    print(f"Error loading recommendation image: {e}")
                    error_label = ttk.Label(game_frame, text="Image unavailable")
                    error_label.pack(pady=5)
                    
        except Exception as e:
            print(f"Error getting recommendations: {e}")
            error_label = ttk.Label(
                self.recommended_games_frame, 
                text=str(e),
                font=('Arial', 11),
                wraplength=400,
                justify='center'
            )
            error_label.pack(pady=20)

# Create and run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = GameSearchApp(root)
    root.mainloop()