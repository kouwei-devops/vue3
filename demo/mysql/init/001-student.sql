USE fastapi;

CREATE TABLE IF NOT EXISTS student (
  id INT NOT NULL AUTO_INCREMENT,
  num VARCHAR(255) NULL,
  name VARCHAR(255) NULL,
  address VARCHAR(255) NULL,
  iphone VARCHAR(255) NULL,
  cluster_id VARCHAR(255) NULL,
  start_date DATE NULL,
  end_date DATE NULL,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO student (id, num, name, address, iphone, cluster_id, start_date, end_date) VALUES
  (1001, '12.6T', 'liuyang', '/lustre/home/liuyang', '16T', '8581', DATE_SUB(CURDATE(), INTERVAL 12 DAY), DATE_ADD(CURDATE(), INTERVAL 18 DAY)),
  (1002, '18.4T', 'wangdi', '/lustre/project/wangdi', '20T', '8581', DATE_SUB(CURDATE(), INTERVAL 5 DAY), DATE_ADD(CURDATE(), INTERVAL 35 DAY)),
  (1003, '4.1T', 'chenrui', '/lustre/share/chenrui', '12T', '8581', DATE_SUB(CURDATE(), INTERVAL 20 DAY), DATE_ADD(CURDATE(), INTERVAL 10 DAY)),
  (1004, '29.0T', 'sunmo', '/lustre/archive/sunmo', '32T', '8581', DATE_SUB(CURDATE(), INTERVAL 45 DAY), DATE_SUB(CURDATE(), INTERVAL 5 DAY)),
  (1005, '7.8T', 'gaojie', '/lustre/home/gaojie', '14T', '8581', DATE_SUB(CURDATE(), INTERVAL 25 DAY), DATE_ADD(CURDATE(), INTERVAL 5 DAY)),
  (1006, '1.9T', 'zhaolin', '/lustre/team/zhaolin', '8T', '8581', DATE_SUB(CURDATE(), INTERVAL 8 DAY), DATE_ADD(CURDATE(), INTERVAL 3 DAY)),
  (2001, '6.3T', 'liuxin', '/lustre/home/liuxin', '10T', '9654', DATE_SUB(CURDATE(), INTERVAL 6 DAY), DATE_ADD(CURDATE(), INTERVAL 22 DAY)),
  (2002, '15.0T', 'heyan', '/lustre/project/heyan', '18T', '9654', DATE_SUB(CURDATE(), INTERVAL 15 DAY), DATE_ADD(CURDATE(), INTERVAL 7 DAY)),
  (2003, '2.4T', 'shiqi', '/lustre/home/shiqi', '8T', '9654', DATE_SUB(CURDATE(), INTERVAL 42 DAY), DATE_SUB(CURDATE(), INTERVAL 12 DAY)),
  (2004, '24.7T', 'tangrui', '/lustre/archive/tangrui', '28T', '9654', DATE_SUB(CURDATE(), INTERVAL 31 DAY), DATE_SUB(CURDATE(), INTERVAL 1 DAY)),
  (2005, '9.1T', 'moyan', '/lustre/share/moyan', '12T', '9654', DATE_SUB(CURDATE(), INTERVAL 33 DAY), DATE_SUB(CURDATE(), INTERVAL 3 DAY)),
  (2006, '3.2T', 'wenhao', '/lustre/home/wenhao', '6T', '9654', DATE_SUB(CURDATE(), INTERVAL 9 DAY), DATE_ADD(CURDATE(), INTERVAL 1 DAY))
ON DUPLICATE KEY UPDATE
  num = VALUES(num),
  name = VALUES(name),
  address = VALUES(address),
  iphone = VALUES(iphone),
  cluster_id = VALUES(cluster_id),
  start_date = VALUES(start_date),
  end_date = VALUES(end_date);
