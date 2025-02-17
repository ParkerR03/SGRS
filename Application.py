import tkinter as tk
from tkinter import ttk
import pandas as pd
from PIL import Image, ImageTk
import requests
from io import BytesIO
from recfunctions import get_recommendations, get_game_id, rec_data


class GameSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Game Recommendation System")
        
        # Make window fullscreen
        self.root.state('zoomed')  # For Windows
        # self.root.attributes('-zoomed', True)  # For Linux
        # self.root.attributes('-fullscreen', True)  # For Mac (or alternative for all platforms)
        
        # Configure both columns to have equal weight
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=0)  # scrollbar column
        self.root.grid_rowconfigure(0, weight=1)
        
        # Import recommendation functions and data
        self.get_recommendations = get_recommendations
        self.get_game_id = get_game_id
        self.rec_data = rec_data
        
        # Load the games data
        self.data = pd.read_csv('Data/rec_allgames.csv')
        self.selected_games = []
        
        # Create main container frame
        self.container = ttk.Frame(root)
        self.container.grid(row=0, column=0, columnspan=2, sticky="nsew")
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)
        
        # Create canvas with scrollbar
        self.canvas = tk.Canvas(self.container)
        self.scrollbar = ttk.Scrollbar(self.container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        # Configure the canvas
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=(0, 0, e.width, e.height)  # Set top boundary to 0
            )
        )
        
        # Add middle-click scrolling bindings
        self.canvas.bind('<Button-2>', self._start_scroll)  # Middle click
        self.canvas.bind('<B2-Motion>', self._do_scroll)    # Middle click and drag
        self.canvas.bind('<MouseWheel>', self._on_mousewheel)  # Mouse wheel
        
        # For Linux systems that use Button-4 and Button-5 for mouse wheel
        self.canvas.bind('<Button-4>', lambda e: self.canvas.yview_scroll(-1, 'units'))
        self.canvas.bind('<Button-5>', lambda e: self.canvas.yview_scroll(1, 'units'))
        
        # Center the window in the canvas
        self.canvas_frame = self.canvas.create_window(
            (0, 0),
            window=self.scrollable_frame,
            anchor="nw",
            width=self.canvas.winfo_width()  # Make frame fill canvas width
        )
        
        # Update canvas width when window is resized
        self.canvas.bind('<Configure>', self.on_canvas_configure)
        
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Pack the scrollbar and canvas
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Configure scrollable_frame to center its contents
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        
        # Create main frame inside scrollable frame
        self.main_frame = ttk.Frame(self.scrollable_frame)
        self.main_frame.grid(row=0, column=0, sticky="n", padx=20)
        
        # Add title/instructions with larger font and padding
        self.instructions = ttk.Label(
            self.main_frame, 
            text="Game Recommendation System\nSelect up to 3 games you enjoy to receive recommendations",
            font=('Arial', 14),
            justify='center'
        )
        self.instructions.grid(row=0, column=0, columnspan=2, padx=20, pady=20)
        
        # Add filters frame
        self.filters_frame = ttk.Frame(self.main_frame)
        self.filters_frame.grid(row=1, column=0, columnspan=2, pady=(0, 20))
        
        # Number of recommendations selector
        self.rec_label = ttk.Label(
            self.filters_frame,
            text="Number of recommendations:",
            font=('Arial', 11)
        )
        self.rec_label.pack(side='left', padx=5)
        
        self.rec_count = ttk.Combobox(
            self.filters_frame,
            values=[5, 6, 7, 8, 9, 10],
            width=5,
            state='readonly'
        )
        self.rec_count.set(5)
        self.rec_count.pack(side='left', padx=(0, 20))
        
        # Price filter
        self.price_label = ttk.Label(
            self.filters_frame,
            text="Max price ($):",
            font=('Arial', 11)
        )
        self.price_label.pack(side='left', padx=5)
        
        self.price_var = tk.StringVar()
        self.price_entry = ttk.Entry(
            self.filters_frame,
            textvariable=self.price_var,
            width=5
        )
        self.price_entry.pack(side='left', padx=(0, 20))
        
        # Wilson score filter
        self.wilson_label = ttk.Label(
            self.filters_frame,
            text="Min wilson score:",
            font=('Arial', 11)
        )
        self.wilson_label.pack(side='left', padx=5)
        
        wilson_values = [round(x/10, 1) for x in range(0, 10)]  # Creates [0.0, 0.1, 0.2, ..., 0.9]
        self.wilson_var = ttk.Combobox(
            self.filters_frame,
            values=wilson_values,
            width=5,
            state='readonly'
        )
        self.wilson_var.pack(side='left')
        
        # Create main container frame
        self.left_frame = ttk.Frame(self.main_frame)
        self.left_frame.grid(row=2, column=0, columnspan=2, padx=50, pady=10)
        
        # Configure column weight to center content
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)  # scrollbar column
        
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
        
        # Configure left_frame to center its contents
        self.left_frame.grid_columnconfigure(0, weight=1)
        
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
        
        # Add listbox scroll binding
        self.listbox.bind('<MouseWheel>', self._on_listbox_scroll)
        self.listbox.bind('<Button-4>', lambda e: self._on_listbox_scroll_linux(e, -1))
        self.listbox.bind('<Button-5>', lambda e: self._on_listbox_scroll_linux(e, 1))
        
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
        
        # Add selected listbox scroll binding
        self.selected_listbox.bind('<MouseWheel>', self._on_listbox_scroll)
        self.selected_listbox.bind('<Button-4>', lambda e: self._on_listbox_scroll_linux(e, -1))
        self.selected_listbox.bind('<Button-5>', lambda e: self._on_listbox_scroll_linux(e, 1))
        
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
        self.recommend_button.grid(row=3, column=0, columnspan=2, pady=30)
        
        # Recommendations frame
        self.recommendations_frame = ttk.Frame(self.main_frame)
        self.recommendations_frame.grid(row=4, column=0, columnspan=2, padx=20, pady=20, sticky='nsew')
        
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
        
        # Add mousewheel bindings to all relevant widgets
        widgets_to_bind = [self.root, self.canvas, self.scrollable_frame, 
                          self.main_frame, self.left_frame]
        
        for widget in widgets_to_bind:
            widget.bind('<MouseWheel>', self._on_mousewheel)  # Windows/MacOS
            widget.bind('<Button-4>', lambda e: self.canvas.yview_scroll(-1, 'units'))  # Linux
            widget.bind('<Button-5>', lambda e: self.canvas.yview_scroll(1, 'units'))   # Linux
        
        # Bind mousewheel for any future widgets in the scrollable frame
        self.scrollable_frame.bind_all('<MouseWheel>', self._on_mousewheel)
        self.scrollable_frame.bind_all('<Button-4>', lambda e: self.canvas.yview_scroll(-1, 'units'))
        self.scrollable_frame.bind_all('<Button-5>', lambda e: self.canvas.yview_scroll(1, 'units'))
        
    def _start_scroll(self, event):
        """Store the initial position when middle click is pressed"""
        self.canvas.scan_mark(event.x, event.y)

    def _do_scroll(self, event):
        """Drag the canvas content when middle click is held"""
        self.canvas.scan_dragto(event.x, event.y, gain=1)

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
            # Sort matches by wilson_score in descending order
            matches = matches.sort_values('wilson_score', ascending=False)
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
        
        # Enable recommend button if at least one game is selected
        if len(self.selected_games) > 0:
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
            
            if len(game_ids) < 1:
                raise ValueError("Please select at least one game for recommendations.")
            
            print(f"Processing recommendations for game IDs: {game_ids}")
            
            # Get filter values
            max_price = None
            if self.price_var.get().strip():
                try:
                    max_price = float(self.price_var.get())
                except ValueError:
                    raise ValueError("Invalid price value")
                
            min_wilson = None
            if self.wilson_var.get():
                try:
                    min_wilson = float(self.wilson_var.get())
                except ValueError:
                    raise ValueError("Invalid wilson score value")
            
            # Get recommendations using the existing function
            n_recommendations = int(self.rec_count.get())
            recommended_indices, similarity_scores = self.get_recommendations(
                game_ids, 
                n=n_recommendations,
                max_price=max_price,
                min_wilson_score=min_wilson
            )
            
            if not recommended_indices:
                raise ValueError("No recommendations found matching the specified criteria")
            
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
                row = idx // 3  # Integer division to determine row
                col = idx % 3   # Modulo to determine column
                
                game_frame = ttk.Frame(cards_frame)
                game_frame.grid(row=row, column=col, padx=20, pady=5)
                
                # Add game name and similarity score
                name_label = ttk.Label(
                    game_frame, 
                    text=f"{game['Name']}\nSimilarity: {similarity_scores[idx]:.2f} | Price: ${game['Price']:.2f}",
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

    def on_canvas_configure(self, event):
        """Update the canvas window size when the canvas is resized"""
        # Update the width of the canvas window
        self.canvas.itemconfig(self.canvas_frame, width=event.width)

    def _on_listbox_scroll(self, event):
        """Handle mousewheel scrolling for listboxes"""
        widget = event.widget
        widget.yview_scroll(int(-1*(event.delta/120)), "units")
        return "break"  # Prevents event from propagating to parent

    def _on_listbox_scroll_linux(self, event, direction):
        """Handle mousewheel scrolling for listboxes on Linux"""
        widget = event.widget
        widget.yview_scroll(direction, "units")
        return "break"  # Prevents event from propagating to parent

# Create and run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = GameSearchApp(root)
    root.mainloop()