export const API_ROUTES = {
    
    AUTH: {
        LOGIN: '/auth/login',
        REGISTER: '/auth/register',
        REFRESH_TOKEN: '/auth/refresh',
        USER_PROFILE: '/auth/profile',        // GET current user's profile
        UPDATE_PROFILE: '/auth/profile/update',  // PUT update current user's profile
    },
    USERS: {
        LIST: '/users',           // GET all users
        CREATE: '/users/create',   // POST create a user
        UPDATE: (id) => `/users/${id}/update`,  // PUT update a user by ID
        DELETE: (id) => `/users/${id}/delete`,  // DELETE a user by ID
    },
    TEAMS: {
        LIST: '/teams',
        CREATE: '/teams/create',
        UPDATE: (id) => `/teams/${id}/update`,
        DELETE: (id) => `/teams/${id}/delete`,
    },
    CLIENTS: {
        LIST: '/clients',
        CREATE: '/clients/create',
        UPDATE: (id) => `/clients/${id}/update`,
        DELETE: (id) => `/clients/${id}/delete`,
    },
    MEETINGS: {
        LIST: '/meetings',
        CREATE: '/meetings/create',
        UPDATE: (id) => `/meetings/${id}/update`,
        DELETE: (id) => `/meetings/${id}/delete`,
    },
    CALENDAR: {
        LIST: '/calendar/events',
        CREATE: '/calendar/events/create',
        UPDATE: (id) => `/calendar/events/${id}/update`,
        DELETE: (id) => `/calendar/events/${id}/delete`,
    },
    TASKS: {
        LIST: '/tasks',
        CREATE: '/tasks/create',
        UPDATE: (id) => `/tasks/${id}/update`,
        DELETE: (id) => `/tasks/${id}/delete`,
    }
};

1. pending forgot password route

user 1 = y3333
user 2 = y4444
user 3 = y5555
user 4 = y6666
user 5 = y7777
user 6 = y8888
user 7 = y9999
user 8 = y1111
user 9 = y0000

// set password 
{
    "username": "yemani510",
    "password": "y2222"
}
{
    "username": "lataj60480",
    "password": "y3333"
}
lataj60480
// client form data format
{
    "business_name": "ABC Corp",
    "contact_person": "John Doe",
    "business_details": "A company specializing in innovative solutions.",
    "brand_key_points": "Innovation, Customer Service, Reliability",
    "business_address": "123 Main St, Springfield, IL",
    "brand_guidelines_link": "https://example.com/brand-guidelines",
    "business_whatsapp_number": "+1234567890",
    "goals_objectives": "Increase market share and customer retention",
    "business_email_address": "contact@abccorp.com",
    "target_region": "North America",
    "brand_guidelines_notes": "Follow brand colors and tone strictly.",
    "business_offerings": "services + products",  # or "services", "products", "other"
    "list_down_field": "Customized services, technology integration",
    "ugc_drive_link": "https://drive.google.com/drive/folders/example",
    "business_website": "https://www.abccorp.com",
    "social_handles": {
        "facebook": "https://www.facebook.com/abccorp",
        "instagram": "https://www.instagram.com/abccorp",
        "other": [
            "https://www.linkedin.com/company/abccorp",
            "https://twitter.com/abccorp"
        ]
    },
    "additional_notes": "Ensure timely delivery of social media posts."
}


// webdevdata 
{
    "client": 1, 
    "website_type": "ecommerce",  
    "num_of_products": 50, 
    "membership": "yes", 
    "website_structure": "Homepage, About Us, Contact Us, Products",
    "design_preference": "Minimalistic and clean design with a blue color palette",
    "domain": "yes", 
    "domain_info": "example.com",  
    "hosting": "yes", 
    "hosting_info": "Hostgator with unlimited bandwidth",  
    "graphic_assets": "yes",  
    "is_regular_update": "yes",  
    "is_self_update": "no", 
    "additional_notes": "We will require regular SEO updates on the blog section."
  }
  
// CALENDER DATA 
  {
    "date": "2024-09-20",
    "post_count": 1,
    "type": "post",
    "category": "Marketing",
    "cta": "Click here to learn more!",
    "resource": "https://example.com/resource",
    "tagline": "Best Post of the Year",
    "caption": "This is an amazing caption that will grab attention!",
    "hashtags": "#Marketing, #SMM, #BusinessGrowth",
    "creatives": "https://example.com/creatives.png",
    "eng_hooks": "What are your thoughts on this?",
    "internal_status": "pending",
    "client_approval": false,
    "comments": "The client liked the creative.",
    "collaboration": "Working with Team A to get more insights."
}
//  TEAM CREATION 

{
    "name": "Marketing Team",
    "description": "Handles all marketing activities.",
    "members": [
        {
            "user_id": 1
        },
        {
            "user_id": 2
        }
    ]
}