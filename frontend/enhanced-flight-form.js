// Enhanced Flight Form with Better Error Handling
// Copy this code into your Lovable project

/**
 * Submits flight data to the database for the authenticated user.
 *
 * Verifies user authentication, constructs a flight record from the provided form data, and inserts it into the 'flights' table. Throws an error if authentication fails or the database operation is unsuccessful.
 *
 * @param {Object} formData - The flight form data, including origin, destination, departure and return dates, and price threshold.
 * @returns {Object} The inserted flight record.
 */
async function submitFlight(formData) {
    try {
        // First, verify authentication
        const { data: { session }, error: sessionError } = await supabase.auth.getSession();
        
        if (sessionError) {
            console.error('Session error:', sessionError);
            throw new Error('Authentication error. Please log in again.');
        }
        
        if (!session?.user) {
            throw new Error('Please log in to save flights.');
        }

        console.log('Authenticated user:', session.user.id);

        // Prepare flight data
        const flightData = {
            user_id: session.user.id, // Use auth.uid() directly
            origin: formData.origin,
            destination: formData.destination,
            departure_date: formData.departure_date,
            return_date: formData.return_date || null,
            price_threshold: parseFloat(formData.price_threshold),
            created_at: new Date().toISOString()
        };

        console.log('Submitting flight data:', flightData);

        // Insert flight record
        const { data, error } = await supabase
            .from('flights')
            .insert([flightData])
            .select();

        if (error) {
            console.error('Database error:', error);
            throw new Error(`Failed to save flight: ${error.message}`);
        }

        console.log('Flight saved successfully:', data);
        return data[0];

    } catch (error) {
        console.error('Submit flight error:', error);
        throw error;
    }
}

/**
 * Initializes the flight form submission handler, managing UI feedback and invoking flight data submission.
 *
 * Attaches a submit event listener to the flight form, handles form data extraction, disables the submit button during processing, displays success or error messages, and resets the form upon successful submission.
 */
function setupFlightForm() {
    const form = document.getElementById('flight-form');
    if (!form) {
        console.error('Flight form not found');
        return;
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const submitButton = e.target.querySelector('button[type="submit"]');
        const errorDiv = document.getElementById('error-message');
        const successDiv = document.getElementById('success-message');
        
        try {
            // Show loading state
            submitButton.disabled = true;
            submitButton.textContent = 'Saving...';
            if (errorDiv) errorDiv.style.display = 'none';
            if (successDiv) successDiv.style.display = 'none';
            
            // Get form data
            const formData = new FormData(e.target);
            const flightData = Object.fromEntries(formData);
            
            // Submit flight
            await submitFlight(flightData);
            
            // Show success message
            if (successDiv) {
                successDiv.textContent = 'Flight saved successfully!';
                successDiv.style.display = 'block';
            }
            
            // Reset form
            e.target.reset();
            
        } catch (error) {
            // Show error message
            if (errorDiv) {
                errorDiv.textContent = error.message;
                errorDiv.style.display = 'block';
            }
            console.error('Form submission error:', error);
        } finally {
            // Reset button
            submitButton.disabled = false;
            submitButton.textContent = 'Save Flight';
        }
    });
}

/**
 * Logs the current authentication session and user details, and tests database connectivity by querying the 'flights' table.
 */
async function debugAuth() {
    try {
        const { data: { session }, error } = await supabase.auth.getSession();
        console.log('Current session:', session);
        console.log('User ID:', session?.user?.id);
        console.log('User email:', session?.user?.email);
        
        if (session?.user) {
            // Test database connection
            const { data, error: dbError } = await supabase
                .from('flights')
                .select('*')
                .limit(1);
                
            console.log('Database test result:', { data, error: dbError });
        }
    } catch (error) {
        console.error('Debug error:', error);
    }
}

/**
 * Checks for the existence of the authenticated user's profile in the 'users' table and logs the result.
 *
 * If no user is authenticated, logs a message and exits. Logs the retrieved user profile data or any errors encountered during the process.
 */
async function checkUserProfile() {
    try {
        const { data: { session } } = await supabase.auth.getSession();
        if (!session?.user) {
            console.log('No authenticated user');
            return;
        }
        
        const { data, error } = await supabase
            .from('users')
            .select('*')
            .eq('id', session.user.id);
        console.log('User profile:', { data, error });
    } catch (error) {
        console.error('Check user profile error:', error);
    }
}

/**
 * Attempts to insert a test flight record into the 'flights' table for the authenticated user and logs the result.
 *
 * If no user is authenticated, logs a message and exits. Logs any errors encountered during the process.
 */
async function testFlightInsert() {
    try {
        const { data: { session } } = await supabase.auth.getSession();
        if (!session?.user) {
            console.log('No authenticated user');
            return;
        }
        
        const { data, error } = await supabase
            .from('flights')
            .insert([{
                user_id: session.user.id,
                origin: 'SLC',
                destination: 'LAX',
                departure_date: '2025-03-15',
                price_threshold: 500
            }])
            .select();
        console.log('Flight insert test:', { data, error });
    } catch (error) {
        console.error('Test flight insert error:', error);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    setupFlightForm();
    
    // Make debugging functions available globally
    window.debugAuth = debugAuth;
    window.checkUserProfile = checkUserProfile;
    window.testFlightInsert = testFlightInsert;
});

// Auto-initialize if DOM is already loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupFlightForm);
} else {
    setupFlightForm();
}