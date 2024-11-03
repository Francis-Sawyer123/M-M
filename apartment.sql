-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Nov 03, 2024 at 05:01 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `apartment`
--

-- --------------------------------------------------------

--
-- Table structure for table `apartmentanalytics`
--

CREATE TABLE IF NOT EXISTS `apartmentanalytics` (
  `graph_id` int(10) NOT NULL AUTO_INCREMENT,
  `today` date NOT NULL,
  `has_active` int(10) NOT NULL,
  PRIMARY KEY (`graph_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- RELATIONSHIPS FOR TABLE `apartmentanalytics`:
--

-- --------------------------------------------------------

--
-- Table structure for table `apartmentsingup`
--

CREATE TABLE IF NOT EXISTS `apartmentsingup` (
  `userid` int(10) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `address` varchar(255) NOT NULL,
  `contact_number` varchar(255) NOT NULL,
  `plate_number` varchar(255) DEFAULT NULL,
  `roomNumber` varchar(255) NOT NULL,
  `ProfilePic` varchar(255) NOT NULL,
  PRIMARY KEY (`userid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- RELATIONSHIPS FOR TABLE `apartmentsingup`:
--

-- --------------------------------------------------------

--
-- Table structure for table `apartment_occupancy`
--

CREATE TABLE IF NOT EXISTS `apartment_occupancy` (
  `Apartment_id` int(10) NOT NULL AUTO_INCREMENT,
  `Last_inspect` date DEFAULT NULL,
  `condition_status` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`Apartment_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- RELATIONSHIPS FOR TABLE `apartment_occupancy`:
--   `Apartment_id`
--       `room_avail` -> `room_id`
--

-- --------------------------------------------------------

--
-- Table structure for table `emergency_records`
--

CREATE TABLE IF NOT EXISTS `emergency_records` (
  `emergency_id` int(10) NOT NULL AUTO_INCREMENT,
  `disaster` varchar(255) NOT NULL,
  `happen_date` date DEFAULT NULL,
  `Unitroom` varchar(255) DEFAULT NULL,
  `description` varchar(255) NOT NULL,
  `status_completion` varchar(255) NOT NULL,
  PRIMARY KEY (`emergency_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- RELATIONSHIPS FOR TABLE `emergency_records`:
--

-- --------------------------------------------------------

--
-- Table structure for table `lease_inform`
--

CREATE TABLE IF NOT EXISTS `lease_inform` (
  `leaseid` int(10) NOT NULL AUTO_INCREMENT,
  `login_id` int(10) NOT NULL,
  `lease_start` date NOT NULL,
  `lease_end` date NOT NULL,
  `monthly` varchar(255) NOT NULL,
  `deposite` varchar(255) NOT NULL,
  `status` varchar(255) NOT NULL,
  PRIMARY KEY (`leaseid`),
  KEY `idx_login_id` (`login_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- RELATIONSHIPS FOR TABLE `lease_inform`:
--   `login_id`
--       `loginapartment` -> `loginid`
--

-- --------------------------------------------------------

--
-- Table structure for table `lease_request`
--

CREATE TABLE IF NOT EXISTS `lease_request` (
  `leaseRec_id` int(10) NOT NULL AUTO_INCREMENT,
  `login_Id` int(10) NOT NULL,
  `start_date` date NOT NULL,
  `end_date` date NOT NULL,
  `monthly` int(255) NOT NULL,
  `Downpayment` int(255) NOT NULL,
  `Comments` varchar(255) NOT NULL,
  `approval` varchar(255) NOT NULL,
  PRIMARY KEY (`leaseRec_id`),
  KEY `login_Id` (`login_Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- RELATIONSHIPS FOR TABLE `lease_request`:
--   `login_Id`
--       `loginapartment` -> `loginid`
--

-- --------------------------------------------------------

--
-- Table structure for table `loginapartment`
--

CREATE TABLE IF NOT EXISTS `loginapartment` (
  `loginid` int(10) NOT NULL AUTO_INCREMENT,
  `email` varchar(255) NOT NULL,
  `password` varchar(255) NOT NULL,
  `uservalue` int(1) NOT NULL,
  PRIMARY KEY (`loginid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- RELATIONSHIPS FOR TABLE `loginapartment`:
--   `loginid`
--       `apartmentsingup` -> `userid`
--

-- --------------------------------------------------------

--
-- Table structure for table `maintenance`
--

CREATE TABLE IF NOT EXISTS `maintenance` (
  `maintain_id` int(10) NOT NULL AUTO_INCREMENT,
  `login_id` int(10) NOT NULL,
  `maintenance_issue` varchar(255) NOT NULL,
  `priority` varchar(255) NOT NULL,
  `filename` varchar(255) NOT NULL,
  `maintenancedate` date DEFAULT NULL,
  `status` varchar(255) NOT NULL,
  PRIMARY KEY (`maintain_id`),
  KEY `login_id` (`login_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- RELATIONSHIPS FOR TABLE `maintenance`:
--   `login_id`
--       `loginapartment` -> `loginid`
--

-- --------------------------------------------------------

--
-- Table structure for table `room_avail`
--

CREATE TABLE IF NOT EXISTS `room_avail` (
  `room_id` int(10) NOT NULL AUTO_INCREMENT,
  `Unit_name` varchar(255) NOT NULL,
  `RoomNumber` varchar(10) NOT NULL,
  `room_floor` varchar(10) NOT NULL,
  `room_size` varchar(255) NOT NULL,
  `Room_Img` varchar(255) NOT NULL,
  PRIMARY KEY (`room_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- RELATIONSHIPS FOR TABLE `room_avail`:
--

-- --------------------------------------------------------

--
-- Table structure for table `utilities`
--

CREATE TABLE IF NOT EXISTS `utilities` (
  `utilitiesid` int(10) NOT NULL AUTO_INCREMENT,
  `login_id` int(10) NOT NULL,
  `water` int(1) NOT NULL,
  `electricity` int(1) NOT NULL,
  `internet` int(1) NOT NULL,
  PRIMARY KEY (`utilitiesid`),
  KEY `login_id` (`login_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- RELATIONSHIPS FOR TABLE `utilities`:
--   `login_id`
--       `loginapartment` -> `loginid`
--

-- --------------------------------------------------------

--
-- Table structure for table `visitors_apartment`
--

CREATE TABLE IF NOT EXISTS `visitors_apartment` (
  `visit_id` int(10) NOT NULL AUTO_INCREMENT,
  `visitor_name` varchar(255) NOT NULL,
  `visitor_email` varchar(255) NOT NULL,
  `visited_room` varchar(255) NOT NULL,
  `visited_date` date DEFAULT NULL,
  `time_in` varchar(255) NOT NULL,
  `time_out` varchar(255) DEFAULT NULL,
  `visit_reason` varchar(255) NOT NULL,
  `confirmation` varchar(255) NOT NULL,
  PRIMARY KEY (`visit_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- RELATIONSHIPS FOR TABLE `visitors_apartment`:
--

--
-- Constraints for dumped tables
--

--
-- Constraints for table `apartment_occupancy`
--
ALTER TABLE `apartment_occupancy`
  ADD CONSTRAINT `apartment_occupancy_ibfk_1` FOREIGN KEY (`Apartment_id`) REFERENCES `room_avail` (`room_id`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints for table `lease_inform`
--
ALTER TABLE `lease_inform`
  ADD CONSTRAINT `lease_inform_ibfk_1` FOREIGN KEY (`login_id`) REFERENCES `loginapartment` (`loginid`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints for table `lease_request`
--
ALTER TABLE `lease_request`
  ADD CONSTRAINT `lease_request_ibfk_2` FOREIGN KEY (`login_Id`) REFERENCES `loginapartment` (`loginid`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints for table `loginapartment`
--
ALTER TABLE `loginapartment`
  ADD CONSTRAINT `loginapartment_ibfk_1` FOREIGN KEY (`loginid`) REFERENCES `apartmentsingup` (`userid`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints for table `maintenance`
--
ALTER TABLE `maintenance`
  ADD CONSTRAINT `maintenance_ibfk_1` FOREIGN KEY (`login_id`) REFERENCES `loginapartment` (`loginid`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints for table `utilities`
--
ALTER TABLE `utilities`
  ADD CONSTRAINT `utilities_ibfk_1` FOREIGN KEY (`login_id`) REFERENCES `loginapartment` (`loginid`) ON DELETE CASCADE ON UPDATE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
