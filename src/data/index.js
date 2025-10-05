export const fetchNDVIData = async (url) => {
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching NDVI data:', error);
        throw error;
    }
};

export const processNDVIData = (data) => {
    // Process the NDVI data as needed for the application
    return data.map(item => ({
        date: item.date,
        ndvi: item.ndvi,
    }));
};