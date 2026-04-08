import { type Recommendation } from "@/components/RestaurantCard";

interface Filters {
  locations: string[];
  cuisines: string[];
  cost_range: { min: number; max: number };
}

export const MOCK_FILTERS: Filters = {
  locations: ["Indiranagar", "Koramangala", "HSR Layout", "Whitefield", "Jayanagar"],
  cuisines: ["North Indian", "South Indian", "Chinese", "Italian", "Continental"],
  cost_range: { min: 200, max: 3500 },
};

export const MOCK_RECOMMENDATIONS: Recommendation[] = [
  {
    rank: 1,
    name: "The Dreaming Dragon [MOCK]",
    cuisine: "Chinese, Asian",
    rating: 4.8,
    cost_for_two: 1200,
    rest_type: "Casual Dining",
    url: "https://www.zomato.com",
    ai_explanation: "This is a premium match for your love of Asian flavors. Its high rating and curated menu perfectly align with your requested area and budget.",
  },
  {
    rank: 2,
    name: "Saffron Skies [MOCK]",
    cuisine: "North Indian, Mughlai",
    rating: 4.6,
    cost_for_two: 1500,
    rest_type: "Fine Dining",
    url: "https://www.zomato.com",
    ai_explanation: "Offers an exquisite North Indian experience. The elegant ambiance makes it perfect for your preference for a high-quality, authentic meal.",
  },
  {
    rank: 3,
    name: "Pasta Paradise [MOCK]",
    cuisine: "Italian",
    rating: 4.4,
    cost_for_two: 900,
    rest_type: "Cafe",
    url: "https://www.zomato.com",
    ai_explanation: "A top-rated Italian spot that fits comfortably within your budget while maintaining exceptional quality standards.",
  },
  {
    rank: 4,
    name: "Coastal Cravings [MOCK]",
    cuisine: "South Indian, Seafood",
    rating: 4.3,
    cost_for_two: 800,
    rest_type: "Quick Bites",
    url: "https://www.zomato.com",
    ai_explanation: "Ideal for a quick yet flavorful South Indian meal. Great value for money and highly recommended by locals in this area.",
  },
  {
    rank: 5,
    name: "Bistro Blue [MOCK]",
    cuisine: "Continental, French",
    rating: 4.2,
    cost_for_two: 1800,
    rest_type: "Bistro",
    url: "https://www.zomato.com",
    ai_explanation: "A charming continental bistro. Its sophisticated menu provides the variety you requested for your special dining experience.",
  },
];
