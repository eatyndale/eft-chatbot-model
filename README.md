# EFT Chatbot

An Emotional Freedom Technique (EFT) chatbot that provides therapeutic support through guided tapping sessions and emotional analysis.

## 🌟 Features

- **User Authentication**: Secure login and registration system
- **Emotional Analysis**: Real-time emotion detection in user messages
- **Guided Tapping Sessions**: Step-by-step EFT tapping instructions
- **Session Management**: Track and manage user therapy sessions
- **Personalized Responses**: AI-powered responses based on user context
- **Database Integration**: SQLite database for user data and session history

## 🛠️ Technology Stack

- **Backend**: Python
- **AI/ML**: OpenAI GPT-3.5 Turbo (Fine-tuned)
- **Database**: SQLite
- **Authentication**: bcrypt
- **UI Framework**: Gradio
- **NLP Libraries**: 
  - Transformers
  - spaCy
  - NLTK
  - scikit-learn

## 📋 Prerequisites

- Python 3.8 or higher
- OpenAI API key
- Git

## 🚀 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/eatyndale/eft-chatbot-model.git
   cd eft-chatbot-model
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Add your OpenAI API key to `.env`:
     ```
     OPENAI_API_KEY=your_api_key_here
     ```

## 💻 Usage

1. Start the application:
   ```bash
   python main.py
   ```

2. Access the web interface at `http://localhost:7860`

3. Register a new account or login with existing credentials

4. Begin your EFT session with the chatbot

## 📁 Project Structure

## 🔒 Security

- API keys and sensitive data are stored in `.env` file (not committed to repository)
- Passwords are hashed using bcrypt
- User sessions are tracked and managed securely
- Database operations use parameterized queries

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -m 'Add feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- OpenAI for providing the GPT-3.5 Turbo model
- The EFT community for therapeutic insights
- All contributors who have helped improve this project

## 📧 Contact

For questions or support, please open an issue in the GitHub repository.

## 🔄 Updates

- Latest update: March 2024
- Version: 1.0.0
