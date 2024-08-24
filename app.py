import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium import IFrame
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Add a logo at the top of the app
st.image("Vista_Logos/logo-transparent-png.png", width=400)


# Inject custom CSS
# Custom CSS
st.markdown(
    """
    <style>
    /* Change the sidebar background color */
    .css-1d391kg {
        background-color: #e8f4f8;
    }

    /* Change the primary color (e.g., for buttons) */
    .stButton>button {
        background-color: #3498db;
        color: white;
    }

    /* Change the font and text color */
    .stTextInput, .stTextArea, .stSelectbox {
        color: #333333;
        font-family: "Arial", sans-serif;
    }

    /* Customize the map container */
    .folium-container {
        border: 2px solid #3498db;
        border-radius: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)
# Mission Statement
st.markdown(
    """
    ## Our Mission
    **Harvest Hub** is an interactive map that connects people to over 550 food pantries across the city.
    The platform is filterable by days open and borough, ensuring quick access to essential resources when needed most.
    """
)

college_data = pd.read_csv('csv/cuny_food_rows.csv')
df = pd.read_csv('csv/food_rows.csv')

# Streamlit app
st.title('Food Pantry Map')

# Tabs for different views
tabs = st.tabs(["Map View", "Data Table", "Contact a College"])

# Map View
with tabs[0]:
    st.write('Use the filters on the left to select the boroughs and days of the week to display food pantries on the map.')
    
    # Sidebar for filters
    st.sidebar.title('Filter Options')
    
    # Boroughs filter
    boroughs = st.sidebar.multiselect(
        'Select Boroughs',
        options=df['BOROUGH'].unique(),
        default=['Manhattan']  # Default to Manhattan only
    )

    # Days filter using checkboxes inside an expander
    with st.sidebar.expander('Select Days'):
        days = []
        day_column_map = {
            'Monday': 'mon',
            'Tuesday': 'tue',
            'Wednesday': 'wed',
            'Thursday': 'thur',
            'Friday': 'fri',
            'Saturday': 'sat',
            'Sunday': 'sun'
        }
        for day, column in day_column_map.items():
            if st.checkbox(day, value=True):
                days.append(day)
    
    # Create a mask for the selected days
    day_mask = df[[day_column_map[day] for day in days]].any(axis=1)
    
    # Apply filters
    filtered_df = df[(df['BOROUGH'].isin(boroughs)) & day_mask]
    
    # Create a Folium map
    m = folium.Map(location=[filtered_df['LATITUDE'].mean(), filtered_df['LONGITUDE'].mean()], zoom_start=12)
    
    # Custom HTML template for the popup with wider dimensions
    html_template = '''
        <div style="width: 600px; padding: 20px; font-size: 14px; font-family: Arial, sans-serif; border: 1px solid #ddd; border-radius: 8px; box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1);">
            <h4 style="margin-top: 0; color: #333; font-size: 20px;">{name}</h4>
            <p style="margin: 0; color: #555;"><strong>Hours:</strong> {hours}</p>
            <p style="margin: 5px 0; color: #555;"><strong>Phone:</strong> {phone}</p>
            <p style="margin: 0; color: #555;"><strong>Address:</strong> {address}</p>
        </div>
    '''
    
    # Add markers to the map with custom HTML popup
    for _, row in filtered_df.iterrows():
        iframe = IFrame(html_template.format(
            name=row['PROGRAM'],
            hours=row['HOURS'],
            phone=row['ORG PHONE'],
            address=row['FULL ADDRESS']
        ), width=600, height=300)  # Increased width and height
        folium.Marker(
            location=[row['LATITUDE'], row['LONGITUDE']],
            popup=folium.Popup(iframe, max_width=650),
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(m)
    
    # Add a legend
    legend_html = '''
        <div style="position: fixed; bottom: 10px; left: 10px; width: 150px; height: auto; 
        background-color: white; border:2px solid grey; z-index:1000; font-size:14px;
        ">&nbsp; <b>Legend</b> <br>
        &nbsp; <i class="fa fa-circle" style="color:blue"></i>&nbsp; Food Pantry<br>
        </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Render the map in Streamlit
    st_folium(m, width=800, height=600)

# Data Table View
with tabs[1]:
    st.write('Food Pantries')
    st.dataframe(filtered_df)

# Content for Tab 3 (Contact a College form)
with tabs[2]:
    st.title("Contact a College")
    
    # Extract unique college names from the 'School' column
    college_names = college_data['School'].unique().tolist()

    # Form for user input
    with st.form(key='contact_form'):
        selected_college = st.selectbox("Choose a College", options=college_names)
        user_email = st.text_input("Your Email Address")
        message = st.text_area("Your Message")
        submit_button = st.form_submit_button(label='Send Message')

    if submit_button:
        # Check if email and message are provided
        if user_email and message:
            # Find the college email based on the selected college
            college_email = college_data.loc[college_data['School'] == selected_college, 'Email'].values[0]

            # Prepare the email
            msg = MIMEMultipart()
            msg['From'] = user_email
            msg['To'] = college_email
            msg['Subject'] = f"Message from {user_email}"

            # Attach the message body
            msg.attach(MIMEText(message, 'plain'))

            try:
                # Set up the SMTP server (example uses Gmail's SMTP server)
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login("your_email@gmail.com", "your_email_password")
                text = msg.as_string()
                server.sendmail(user_email, college_email, text)
                server.quit()

                st.success(f"Message sent successfully to {selected_college}!")
            except Exception as e:
                st.error(f"Failed to send message. Error: {e}")
        else:
            st.error("Please provide both your email address and a message.")