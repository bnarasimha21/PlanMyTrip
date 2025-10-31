# ✈️ TripXplorer

[![Deploy to DO](https://www.deploytodo.com/do-btn-blue.svg)](https://cloud.digitalocean.com/apps/new?repo=https://github.com/bnarasimha21/TripXplorer/tree/main)

An AI-powered travel planning application that generates personalized itineraries with interactive maps and intelligent conversation features.

## 🌟 Features

### 🎯 **Core Functionality**
- **AI Trip Planning**: Generate custom itineraries based on your interests and destination
- **Interactive Maps**: Visualize your itinerary on beautiful Mapbox maps with custom markers
- **AI Assistant Chatbot**: Ask questions and modify your itinerary through natural conversation

### 🎨 **User Experience**
- **Modern UI**: Professional glassmorphism design with gradient backgrounds
- **Three-Panel Layout**: Controls, map, and itinerary display
- **Responsive Design**: Optimized for desktop and tablet viewing
- **Real-time Updates**: See changes reflected immediately on the map

### 🤖 **AI-Powered Features**
- **Smart Extraction**: Automatically parse trip requests into structured data
- **Contextual Recommendations**: Get place suggestions based on your interests
- **Conversational Interface**: Chat with AI to refine and modify your plans
- **Geocoding Integration**: Automatically locate places on the map

## 🏗️ Architecture

### **Frontend** (React + TypeScript + Vite)
- **Framework**: React 18 with TypeScript
- **Styling**: Tailwind CSS with custom gradients and glassmorphism effects
- **Maps**: Mapbox GL JS for interactive mapping
- **Build Tool**: Vite for fast development and building

### **Backend** (FastAPI + Python)
- **Framework**: FastAPI for high-performance API endpoints
- **AI Integration**: CrewAI agents for intelligent task processing
- **LLM**: OpenAI GPT-4o-mini for natural language processing
- **Geocoding**: Mapbox Geocoding API for location services

## 🚀 Quick Start

### Prerequisites
- **Node.js** 18+ and npm
- **Python** 3.8+
- **OpenAI API Key**
- **Mapbox Access Token**

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/TripXplorer.git
cd TripXplorer
```

### 2. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
# Edit .env and add your OpenAI API key
```

### 3. Frontend Setup
```bash
# Navigate to frontend directory
cd ../frontend

# Install dependencies
npm install

# Create environment file
cp .env.example .env
# Edit .env and add your Mapbox token and API base URL
```

### 4. Environment Configuration

#### Backend `.env`:
```env
OPENAI_API_KEY=your_openai_api_key_here
MAPBOX_API_KEY=your_mapbox_token_here
```

#### Frontend `.env`:
```env
VITE_MAPBOX_TOKEN=your_mapbox_token_here
VITE_API_BASE=http://localhost:8000
```

### 5. Run the Application

#### Start Backend (Terminal 1):
```bash
cd backend
source venv/bin/activate
python3 -m uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

#### Start Frontend (Terminal 2):
```bash
cd frontend
npm run dev
```

Visit `http://localhost:5173` to use the application!

## 📖 Usage Guide

### 📝 **Creating a Trip Request**
1. **Text Input**: Type your request in the text area
2. **Get Details**: Click to extract structured information from your request

### 🗺️ **Generating Your Itinerary**
1. Click "Generate Itinerary" after extracting details
2. Watch as your places appear on the interactive map
3. View detailed information in the right sidebar

### 💬 **Using the AI Assistant**
1. Once your itinerary is generated, use the chatbot to:
   - Add new places: "Add a coffee shop near the Louvre"
   - Remove places: "Remove the restaurant from day 1"
   - Ask questions: "What's the best route between these places?"
   - Get recommendations: "What's nearby the art museum?"

### 🎨 **Map Features**
- **Custom Markers**: Different colors for food (amber) and art (rose) categories
- **Popup Information**: Click markers to see place details
- **Auto-centering**: Map automatically focuses on your itinerary locations
- **Night Theme**: Beautiful dark theme optimized for travel planning

## 🛠️ API Endpoints

### **POST** `/extract`
Extract trip details from natural language input.
```json
{
  "text": "Plan a 2-day art and food tour in Barcelona"
}
```

### **POST** `/itinerary`
Generate a complete itinerary with places and map data.
```json
{
  "city": "Barcelona",
  "interests": "art, food",
  "days": 2
}
```

### **POST** `/modify`
Modify existing itinerary based on user instructions.
```json
{
  "city": "Barcelona",
  "interests": "art, food",
  "days": 2,
  "places": [...],
  "instruction": "Add a tapas restaurant"
}
```

## 🔧 Development

### **Project Structure**
```
TripXplorer/
├── backend/
│   ├── agents.py          # CrewAI agents and tasks
│   ├── api.py            # FastAPI application
│   ├── requirements.txt   # Python dependencies
│   └── .env              # Backend environment variables
├── frontend/
│   ├── src/
│   │   ├── App.tsx       # Main React component
│   │   ├── main.tsx      # React entry point
│   │   └── index.css     # Global styles
│   ├── package.json      # Node.js dependencies
│   └── .env             # Frontend environment variables
└── README.md
```

### **Adding New Features**
1. **Backend**: Add new endpoints in `api.py` and agent logic in `agents.py`
2. **Frontend**: Extend `App.tsx` with new UI components and API calls
3. **Styling**: Use Tailwind CSS classes for consistent design

### **Environment Variables**
- Keep all API keys in `.env` files
- Never commit sensitive credentials to version control
- Use appropriate prefixes (`VITE_` for frontend variables)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and test thoroughly
4. Commit with descriptive messages: `git commit -m "Add new feature"`
5. Push to your fork: `git push origin feature-name`
6. Create a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI** for GPT models and AI capabilities
- **Mapbox** for beautiful mapping services
- **CrewAI** for agent-based task orchestration
- **React** and **FastAPI** communities for excellent frameworks
- **Tailwind CSS** for utility-first styling

## 🐛 Troubleshooting

### **Common Issues**

#### Backend won't start:
- Check if virtual environment is activated
- Verify OpenAI API key is set in `backend/.env`
- Ensure all dependencies are installed: `pip install -r requirements.txt`

#### Frontend shows blank page:
- Check if Mapbox token is set in `frontend/.env`
- Verify backend is running on the correct port
- Check browser console for JavaScript errors



#### Map not displaying:
- Verify Mapbox token is valid and not expired
- Check browser network tab for API errors
- Ensure token has the correct permissions

For more help, please open an issue on GitHub!

---

**Happy Trip Planning!** ✈️🗺️
