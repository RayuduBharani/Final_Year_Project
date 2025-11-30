from flask import Flask, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash
from datetime import datetime
import os

# Import configuration
from config.settings import Config
from config.database import (
    MONGO_CONNECTED, 
    users_collection, 
    jobs_collection, 
    applications_collection
)

# Import utilities
from utils.text_extraction import PDF_SUPPORT, DOCX_SUPPORT

# Import route blueprints
from routes import auth_bp, jobs_bp, applications_bp, analytics_bp


def create_app():
    """Application factory function"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(Config)
    
    # Enable CORS
    CORS(app, supports_credentials=True)
    
    # Create uploads folder if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'resumes'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'job_descriptions'), exist_ok=True)
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(jobs_bp)
    app.register_blueprint(applications_bp)
    app.register_blueprint(analytics_bp)
    
    # Register health check and error handlers
    register_routes(app)
    register_error_handlers(app)
    
    return app


def register_routes(app):
    """Register standalone routes"""
    
    @app.route('/', methods=['GET'])
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'message': 'HR Resume Review Backend API is running!',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0',
            'database': 'MongoDB',
            'mongo_connected': MONGO_CONNECTED,
            'pdf_support': PDF_SUPPORT,
            'docx_support': DOCX_SUPPORT,
            'stats': {
                'total_jobs': jobs_collection.count_documents({}) if MONGO_CONNECTED else 0,
                'total_applications': applications_collection.count_documents({}) if MONGO_CONNECTED else 0
            }
        })


def register_error_handlers(app):
    """Register error handlers"""
    
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'success': False, 'message': 'Resource not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({'success': False, 'message': 'Internal server error'}), 500
    
    @app.errorhandler(413)
    def file_too_large(e):
        return jsonify({'success': False, 'message': 'File too large. Maximum size is 16MB'}), 413


def init_default_data():
    """Initialize database with default HR user only"""
    if users_collection.count_documents({}) == 0:
        users_collection.insert_one({
            'email': 'hr@company.com',
            'password': generate_password_hash('hr123'),
            'name': 'HR Admin',
            'role': 'admin',
            'created_at': datetime.now()
        })
        print("✅ Created default HR user: hr@company.com / hr123")
    else:
        print("✅ HR user already exists")


# Create the application instance
app = create_app()


if __name__ == '__main__':
    print("\n" + "="*65)
    print("🚀  HR Resume Review Backend Server (MongoDB)")
    print("="*65)
    print(f"\n📁 Upload folder: {app.config['UPLOAD_FOLDER']}")
    print(f"🔌 MongoDB Connected: {'✅ Yes' if MONGO_CONNECTED else '❌ No'}")
    print(f"📄 PDF Support: {'✅ Enabled' if PDF_SUPPORT else '❌ Disabled'}")
    print(f"📝 DOCX Support: {'✅ Enabled' if DOCX_SUPPORT else '❌ Disabled'}")
    
    if MONGO_CONNECTED:
        # Initialize default data
        init_default_data()
    
    print("\n" + "-"*65)
    print("📌 API Endpoints:")
    print("-"*65)
    print("\n🔐 Authentication:")
    print("   POST   /api/auth/login     - Login with email/password")
    print("   POST   /api/auth/logout    - Logout and invalidate session")
    print("   POST   /api/auth/register  - Register new HR user")
    print("   GET    /api/auth/verify    - Verify session token")
    print("\n💼 Jobs:")
    print("   GET    /api/jobs           - List all jobs")
    print("   POST   /api/jobs           - Create new job [Auth]")
    print("   GET    /api/jobs/<id>      - Get job details")
    print("   PUT    /api/jobs/<id>      - Update job [Auth]")
    print("   DELETE /api/jobs/<id>      - Delete job [Auth]")
    print("\n📝 Applications:")
    print("   GET    /api/applications         - List applications")
    print("   POST   /api/jobs/<id>/apply      - Submit application")
    print("   PUT    /api/applications/<id>/status - Update status [Auth]")
    print("   POST   /api/applications/<id>/rescore - Recalculate ATS scores [Auth]")
    print("   GET    /api/applications/<id>/ats-breakdown - Get detailed ATS breakdown")
    print("   POST   /api/jobs/<id>/rescore-all - Rescore all applications [Auth]")
    print("\n📊 Analytics:")
    print("   GET    /api/analytics/overview   - Dashboard overview [Auth]")
    print("   GET    /api/analytics/job/<id>   - Job analytics [Auth]")
    print("\n" + "-"*65)
    print("🔑 Default HR Login Credentials:")
    print("   Email:    hr@company.com")
    print("   Password: hr123")
    print("="*65 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
