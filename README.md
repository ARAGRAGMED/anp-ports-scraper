# ANP Ports Vessel Scraper 🇲🇦

A comprehensive web scraper for monitoring Moroccan port activities from the Agence Nationale des Ports (ANP), specifically targeting vessel movements, port operations, and maritime traffic data.

## 🎯 Features

### Core Functionality
- **🔍 Smart API Scraping**: Scrapes ANP vessel movement data via REST API
- **🎯 Intelligent Data Filtering**: Advanced filtering logic for vessel types and operators
- **🧹 Duplicate Prevention**: Robust deduplication using vessel IDs and timestamps
- **📊 Beautiful Dashboard**: Modern web interface with real-time data visualization
- **🔄 API Integration**: RESTful API for programmatic access

### Data Filtering Logic
- **Group A (Vessel Types)**: **OPTIONAL** - VRAQUIER, CHIMIQUIER, TANKER, etc.
- **Group B (Operators)**: **OPTIONAL** - OCP, MARSA MAROC, SOMAPORT, etc.
- **Group C (Ports/Locations)**: **MANDATORY** - At least one required
  - **Group C**: Ports (CASABLANCA, SAFI, TANGER MED, etc.)

### Advanced Features
- **🎨 Color-coded Categories**: Visual display of vessel types and operators in dashboard
- **📅 Real-time Updates**: Live data from ANP API
- **🔧 CLI Tools**: Command-line interface for automation
- **📈 Export Capabilities**: CSV export with filtering options
- **🌐 Vercel Deployment**: Ready for cloud deployment

## 🚀 **Deployment & Usage**

### **Local Development (Recommended for Full Functionality)**

For complete functionality with persistent data storage:

```bash
# Clone the repository
git clone <repository-url>
cd anp-ports-scraper

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp env.example .env
# Edit .env with your ANP API credentials if needed

# Run the scraper
python3 run_scraper.py --force-update

# Start the web dashboard
python3 src/main.py
# Open http://localhost:8000
```

**✅ Local Benefits:**
- Persistent data storage in `data/` folder
- Full scraping history maintained
- No data loss between runs
- Complete functionality

### **Vercel Deployment (Limited Functionality)**

The project can be deployed to Vercel, but with **significant limitations**:

**⚠️ Vercel Limitations:**
- Data is stored in `/tmp` directory (temporary)
- Data gets cleared between function invocations
- No persistent storage between requests
- Dashboard shows 0 results after page refresh

**🔧 Vercel Setup:**
```bash
# Deploy to Vercel
vercel --prod

# Environment variables in Vercel dashboard:
ANP_API_URL=https://www.anp.org.ma//_vti_bin/WS/Service.svc/mvmnv/all
```

**📊 Vercel Use Case:**
- Testing the scraper functionality
- Demonstrating the filtering logic
- Temporary data viewing
- **NOT suitable for production data collection**

## 📊 Dashboard Features

### Main Interface
- **📈 KPI Cards**: Total vessels, active vessels, last update time, status
- **🔍 Advanced Filters**: Date range, vessel type, operator, port, search
- **📋 Interactive Table**: Sortable results with color-coded categories
- **📊 Charts**: Timeline and vessel type visualizations

### Category Display
- **🛡️ Blue badges**: Vessel types (VRAQUIER, CHIMIQUIER, TANKER, etc.)
- **🧪 Orange badges**: Operators (OCP, MARSA MAROC, etc.)
- **🌍 Green badges**: Ports/Locations (CASABLANCA, SAFI, etc.)

### Actions
- **🔄 Update Now**: Trigger immediate data update from ANP API
- **📥 Export CSV**: Download filtered results
- **👁️ View Details**: Inspect raw vessel data
- **🔗 External Links**: Direct links to vessel tracking

## 🔧 API Endpoints

### Core Endpoints
```bash
# Trigger data update
POST /api/update?force_update=true

# Get dashboard data
GET /api/dashboard-data

# Get specific vessel
GET /api/vessels/{vessel_id}

# Export CSV
GET /api/export/csv?start_date=2025-01-01&end_date=2025-12-31

# Get filter options
GET /api/operators
GET /api/ports  
GET /api/vessel-types
```

### Response Format
```json
{
  "status": "success",
  "message": "Successfully updated vessel data",
  "new_vessels": 15,
  "total_vessels": 45,
  "duration_seconds": 2.5,
  "last_update": "2025-01-20T10:30:00Z"
}
```

## 📁 Project Structure

```
anp-ports-scraper/
├── src/
│   ├── main.py                 # FastAPI application
│   ├── scraper.py             # Core scraping logic
│   ├── matcher.py             # Data filtering engine
│   ├── adapters/
│   │   ├── anp_api.py         # ANP API client
│   │   └── __init__.py        # Package initialization
│   └── web/
│       ├── index.html         # Dashboard UI
│       └── app.js             # Frontend JavaScript
├── data/                      # Data storage
├── requirements.txt           # Python dependencies
├── env.example               # Environment configuration
├── run_scraper.py            # CLI interface
├── test_scraper.py           # Test suite
├── vercel.json               # Vercel configuration
└── README.md                 # This file
```

## 🎯 Data Categories

### Group A: Vessel Types (Optional)
- VRAQUIER, CHIMIQUIER, TANKER, PORTE CONTENEUR
- PASSAGERS, GAZIER, PETROLIER, CONVENTIONEL
- Specialized vessel categories

### Group B: Operators (Optional)  
- OCP, MARSA MAROC, SOMAPORT, SOSIPO
- MASS CEREALES, COMATAM, AGEMAFRIC
- Shipping companies and agencies

### Group C: Ports/Locations (Mandatory)
- **Major Ports**: CASABLANCA, SAFI, TANGER MED, AGADIR
- **International Ports**: VANCOUVER, BEAUMONT, NECOCHEA, MALTA
- **European Ports**: DUNKERQUE, ALMERIA, MARSEILLE, VALENCIA

## 🔍 Filtering Logic

The scraper uses advanced filtering with:

### Data Validation
- ✅ Valid vessel names and IMO numbers
- ✅ Proper timestamp formatting
- ✅ Geographic coordinate validation
- ❌ Invalid or corrupted data filtered out

### Filtering Requirements
- **Group C (Ports/Locations)** must have at least 1 match
- **Groups A or B** must have at least 1 match combined
- Vessels matching these criteria are saved and displayed

## 📊 Data Storage

### JSON Format
```json
{
  "nOM_NAVIREField": "EPIPHANIA",
  "nUMERO_ESCALEField": 201463131,
  "nUMERO_LLOYDField": "9104469",
  "oPERATEURField": "MASS CEREALES",
  "pROVField": "VANCOUVER",
  "sITUATIONField": "EN RADE",
  "tYP_NAVIREField": "VRAQUIER",
  "cONSIGNATAIREField": "TRADE NAV",
  "dATE_SITUATIONField": "/Date(1755817200000+0100)/",
  "scraped_at": "2025-01-20T10:30:00.123456",
  "filter_details": {
    "groups_matched": 2,
    "match_score": 3,
    "vessel_type_keywords": ["VRAQUIER"],
    "operator_keywords": [],
    "port_location_keywords": ["VANCOUVER"],
    "matched_snippets": ["VRAQUIER vessel EPIPHANIA from VANCOUVER"]
  }
}
```

### Deduplication
- **Primary**: Vessel Name + Escale Number
- **Secondary**: Lloyd Number + Timestamp
- **Automatic**: Built into scraping process
- **Manual**: `--clean-duplicates` CLI command

## 🌐 Deployment

### Local Development
```bash
# Start development server
cd src && python3 main.py

# Access at http://localhost:8000
```

### Vercel Deployment
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod

# Configure environment variables in Vercel dashboard
```

### Environment Variables
```bash
# Required: ANP API endpoint
ANP_API_URL=https://www.anp.org.ma//_vti_bin/WS/Service.svc/mvmnv/all

# Optional: Application settings
LOG_LEVEL=INFO
DATA_DIR=./data
UPDATE_INTERVAL=300  # 5 minutes
```

## 🔧 Configuration

### Update Parameters
- **Update Interval**: 5 minutes by default (configurable)
- **Data Retention**: 30 days by default (configurable)
- **API Rate Limiting**: Respectful requests with delays

### Category Customization
Edit `src/matcher.py` to modify category groups:
```python
# Add new vessel types
self.vessel_type_keywords.append("NewVesselType")

# Add new operators  
self.operator_keywords.append("NewOperator")

# Add new ports
self.port_location_keywords.append("NewPort")
```

## 🐛 Troubleshooting

### Common Issues

#### No Vessels Found
- Check API endpoint availability
- Verify filtering logic
- Use `--stats` to see what's in the database

#### Duplicates
- Run `python3 run_scraper.py --clean-duplicates`
- Deduplication is automatic in new updates

#### Server Not Starting
- Check if port 8000 is available
- Ensure all dependencies are installed
- Check Python version (3.8+ required)

#### ANP API Connection Issues
- ANP may have rate limiting
- Check API endpoint availability
- Verify network connectivity

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python3 run_scraper.py --force-update
```

## 📈 Performance

### Metrics
- **Update Speed**: ~2-3 seconds for full API response
- **Match Rate**: 100% with current filtering logic
- **Deduplication**: Automatic and efficient
- **Memory Usage**: Low (streaming JSON processing)

### Optimization
- Efficient API calls with proper caching
- Smart deduplication prevents data bloat
- Efficient filtering with compiled regex
- Respectful API usage with delays

## 🤝 Contributing

### Development Setup
```bash
# Fork the repository
git clone <your-fork>
cd anp-ports-scraper

# Create feature branch
git checkout -b feature/new-feature

# Make changes and test
python3 run_scraper.py --force-update

# Commit and push
git commit -m "Add new feature"
git push origin feature/new-feature
```

### Code Style
- Follow PEP 8 for Python code
- Use meaningful variable names
- Add docstrings to functions
- Include type hints where appropriate

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- ANP (Agence Nationale des Ports) for providing public maritime data
- FastAPI for the excellent web framework
- Tabler for the beautiful UI components
- The open-source community for inspiration and tools

## 📞 Support

For questions, issues, or contributions:
- Open an issue on GitHub
- Check the troubleshooting section
- Review the API documentation at `/docs`

---

**Built with ❤️ for Moroccan port monitoring**
