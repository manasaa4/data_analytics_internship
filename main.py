import streamlit as st
import pandas as pd
import plotly.express as px
import openai
from dotenv import load_dotenv
import os
import hashlib


# Load the dataset
df = pd.read_csv("dashboard_data.csv")
# Load environment variables from .env
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
admin_email = os.getenv("ADMIN_EMAIL")

# Utility functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def store_credentials(name, email, password):
    credentials = pd.DataFrame([[name, email, hash_password(password)]], columns=['Name', 'Email', 'Password'])
    try:
        existing_data = pd.read_csv('credentials.csv')
        credentials = pd.concat([existing_data, credentials], ignore_index=True)
    except FileNotFoundError:
        pass
    credentials.to_csv('credentials.csv', index=False)

def validate_credentials(email, password):
    try:
        credentials = pd.read_csv('credentials.csv')
        user = credentials[(credentials['Email'] == email) & (credentials['Password'] == hash_password(password))]
        return user.iloc[0]['Name'] if not user.empty else None
    except FileNotFoundError:
        return None

# Configure Streamlit pages
st.set_page_config(page_title="GDP and Productivity App", layout="wide")


# State management
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user_name = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Login"

# Page navigation logic
if st.session_state.current_page == "Login":
    page_choice = st.sidebar.selectbox("Choose Option", ["Login", "Sign Up"])

    if page_choice == "Sign Up":
        st.title("GDP and Productivity Visualisation App 📈")
        st.markdown("### Sign Up")
        name = st.text_input("Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Sign Up"):
            if name and email and password:
                store_credentials(name, email, password)
                st.success("Account created successfully! Please log in.😄")
            else:
                st.error("Please fill in all fields.😰")

        st.image("img\signup.png", width=350)

    elif page_choice == "Login":
        st.title("GDP and Productivity Visualisation App 📈")
        st.markdown("### Login")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            user_name = validate_credentials(email, password)
            if user_name:
                st.session_state.authenticated = True
                st.session_state.user_name = user_name
                st.session_state.current_page = "Home"
            else:
                st.error("Invalid credentials. Please try again.😰 Or SignIn if account not created!!")

        st.image("img\login.png",  width=400,)

elif st.session_state.current_page == "Home":
    # Sidebar navigation
    page = st.sidebar.selectbox("Navigation", ["Home", "Power BI Dashboard", "Chatbot", "Feedback", "Logout"])

    if page == "Home":
        st.markdown(f" ### Welcome {st.session_state.user_name}!")
        st.title("GDP and Productivity Visualisation App 📈")
        st.image("img\Screenshot 2025-10-19 134910.png", width=700)

        #filters
        cities = df['City'].unique()
        selected_city = st.sidebar.multiselect("Select City:", cities, default=cities)
        year_range = st.sidebar.slider("Select Year Range:", int(df['Year'].min()), int(df['Year'].max()),
                                       (int(df['Year'].min()), int(df['Year'].max())))

        filtered_df = df[(df['City'].isin(selected_city)) & (df['Year'].between(year_range[0], year_range[1]))]

        if filtered_df.empty:
            st.error("No data available. Please select at least one city and a valid year range.")
        else:
            # Calculate key metrics from the dataset
            total_gdp = filtered_df['GDP_Billion'].sum()
            avg_employment_rate = filtered_df['Employment_Rate'].mean()
            highest_gdp_city = filtered_df.groupby('City')['GDP_Billion'].sum().idxmax()

            # Prepare card content with actual values
            card_content = f"""
                        <style>
                        .card {{
                            display: inline-block;
                            padding: 20px;
                            margin: 10px;
                            border-radius: 10px;
                            box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);
                            background-color: #007BFF; /* Primary Blue */
                            width: 250px;
                            text-align: center;
                        }}
                        .card:hover {{
                            transform: scale(1.05); /* Slightly enlarge the card */
                            box-shadow: 0px 6px 12px rgba(0, 0, 0, 0.2); /* Add a stronger shadow on hover */
                        }}
                        .card h3 {{
                            margin: 0;
                            font-size: 24px;
                            color: #FFFFFF;
                        }}
                        .card p {{
                            margin: 5px 0 0;
                            font-size: 16px;
                            color: #FFFFFF;
                        }}
                        </style>

                        <div style="display: flex; justify-content: center; flex-wrap: wrap;">
                            <div class="card">
                                <h3>Total GDP</h3>
                                <p>{total_gdp:,.2f} Billion</p>
                            </div>
                        <div class="card">
                            <h3>Avg Employment Rate</h3>
                            <p>{avg_employment_rate:.2f}%</p>
                            </div>
                            <div class="card">
                                <h3>City with Highest GDP</h3>
                                <p>{highest_gdp_city}</p>
                            </div>
                        </div>
                    """

            # Display cards with the formatted content
            st.markdown(card_content, unsafe_allow_html=True)

            #Line chart for GDP Trends
            st.subheader("GDP Trends")
            gdp_trend = filtered_df.groupby('Year')['GDP_Billion'].sum().reset_index()
            fig = px.line(gdp_trend, x='Year', y='GDP_Billion', title="GDP Trend Over Years")
            fig.update_traces(line=dict(color='#007BFF'))
            st.plotly_chart(fig)

            # Bar Chart: Employment by Sector
            st.subheader("Employment by Sector")

            # Prepare the data for plotting
            sector_employment = filtered_df[['SME_Employment', 'Tourism_Employment', 'ICT_Employment']].mean().reset_index()
            sector_employment.columns = ['Sector', 'Employment Rate']  # Rename columns for clarity

            # Create bar chart
            fig_sector = px.bar(
                sector_employment,
                x='Sector',
                y='Employment Rate',
                labels={'Sector': 'Sector', 'Employment Rate': 'Average Employment Rate'},
                title="Average Employment Rate by Sector",
                color_discrete_sequence=['#1E90FF', '#4682B4', '#87CEEB']
            )

            st.plotly_chart(fig_sector)

            st.subheader("Sectoral Contribution")
            gdp_contribution = filtered_df[['Agriculture GDP', 'SME GDP', 'Tourist_GDP', 'ICT_GDP']].sum()
            blue_colors_pie = ['#1E90FF', '#4682B4', '#87CEEB', '#ADD8E6']
            pie_chart = px.pie(
                values=gdp_contribution,
                names=gdp_contribution.index,
                title="GDP Contribution by Sector",
                color_discrete_sequence=blue_colors_pie
            )
            st.plotly_chart(pie_chart)

            # Insights Section
            st.markdown("## Key Insights")

            # Insight 1: City with the highest average GDP
            highest_avg_gdp_city = (
                filtered_df.groupby('City')['GDP_Billion'].mean().idxmax()
            )
            highest_avg_gdp = filtered_df.groupby('City')['GDP_Billion'].mean().max()

            st.markdown(
                f"""
                <div style="background-color: #87CEEB; padding: 10px; border-radius: 5px; color: #382445;  margin-bottom: 15px;">
                    <strong>1. City with the highest average GDP:</strong> {highest_avg_gdp_city} (${highest_avg_gdp:,.2f} Billion)
                </div>
                """,
                unsafe_allow_html=True
            )

            # Insight 2: Year with the highest total GDP
            highest_gdp_year = filtered_df.groupby('Year')['GDP_Billion'].sum().idxmax()
            highest_gdp_value = filtered_df.groupby('Year')['GDP_Billion'].sum().max()

            st.markdown(
                f"""
                <div style="background-color: #ADD8E6; padding: 10px; border-radius: 5px; color: #56376a; margin-bottom: 15px;">
                    <strong>2. Year with the highest total GDP:</strong> {highest_gdp_year} (${highest_gdp_value:,.2f} Billion)
                </div>
                """,
                unsafe_allow_html=True
            )

            # Insight 3: Sector with the highest average employment
            highest_employment_sector = (
                sector_employment.sort_values(by='Employment Rate', ascending=False).iloc[0]
            )

            st.markdown(
                f"""
                <div style="background-color: #87CEEB; padding: 10px; border-radius: 5px; color: #382445; margin-bottom: 15px;">
                    <strong>3. Sector with the highest average employment:</strong> {highest_employment_sector['Sector']} ({highest_employment_sector['Employment Rate']:.2f}%)
                </div>
                """,
                unsafe_allow_html=True
            )

            # Insight 4: Average youth unemployment rate
            avg_youth_unemployment = filtered_df['Youth_Unemployment_Rate'].mean()
            # Add a concluding remark
            st.markdown(
                f"""
                <div style="background-color: #ADD8E6; padding: 10px; border-radius: 5px; color: #56376a; margin-bottom: 15px;">
                    <strong>4. Average youth unemployment rate:</strong> {avg_youth_unemployment:.2f}%
                </div>
                """,
                unsafe_allow_html=True
            )


    elif page == "Power BI Dashboard":
        st.title("Power BI Dashboard 🌟")
        st.markdown("""
           This page displays an embedded Interactive Power BI report.
           """)
        power_bi_url = "https://app.powerbi.com/view?r=eyJrIjoiNTY3YThiMWYtZDY1Zi00ODM2LTg3YTItNThjY2JiM2I3MGZjIiwidCI6IjBmMjMyOWE4LTkxMmQtNGM5NC1iYzYwLTFjZTI3OWIxNzZlNCJ9"
        st.components.v1.iframe(power_bi_url, width=1000, height=700)

    elif page == "Chatbot":
        st.title("Chatbot 🤖")
        user_input = st.text_input("Ask me anything about GDP!")

        if user_input:
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are an expert on GDP and employment."},
                        {"role": "user", "content": user_input}
                    ],
                    max_tokens=150
                )
                st.write(response['choices'][0]['message']['content'])
            except Exception as e:
                st.error(f"Error: {str(e)}")
        print("\n")
        st.image("img\chatbot.png", width=400)

    elif page == "Feedback":
        st.title("Feedback")

        st.markdown("We value your feedback to improve the application! Please share your thoughts below. 😊")

        # User Inputs
        user_email = st.text_input("Your Email", placeholder="Enter your email address")
        feedback = st.text_area("Your Feedback", placeholder="Write your feedback here...")

        # Feedback Submission Button
        if st.button("Submit Feedback"):
            if user_email and feedback:
                if "@" in user_email:  # Basic email validation
                    try:
                        # store feedback in a CSV file
                        feedback_df = pd.DataFrame([[user_email, feedback, pd.Timestamp.now()]],
                                                   columns=['Email', 'Feedback', 'Timestamp'])
                        try:
                            existing_feedback = pd.read_csv('feedback.csv')
                            feedback_df = pd.concat([existing_feedback, feedback_df], ignore_index=True)
                        except FileNotFoundError:
                            pass

                        feedback_df.to_csv('feedback.csv', index=False)

                        st.success(f"Thank you for your feedback! Submitted on {pd.Timestamp.now():%Y-%m-%d %H:%M:%S}")
                    except Exception as e:
                        st.error(f"An error occurred while sending your feedback: {str(e)}")
                else:
                    st.error("Please enter a valid email address.")
            else:
                st.error("Both fields are required. Please fill them out.")

        st.image("img\Screenshot 2025-10-19 125522.png", width=400)

    elif page == "Logout":
        st.title("Logged Out Successfully 👋")
        st.markdown("You have been logged out. See you again soon!")
        st.image("img\log out.png", width=350)        
        st.session_state.authenticated = False
        st.session_state.user_name = None
        st.session_state.current_page = "Login"