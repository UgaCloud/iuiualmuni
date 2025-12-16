<?php
define( 'DS', DIRECTORY_SEPARATOR );
defined( 'DS' ) or die( 'Error' );

use PHPMailer\PHPMailer\PHPMailer;
//use PHPMailer\PHPMailer\SMTP;
//use PHPMailer\PHPMailer\Exception;

use \DrewM\MailChimp\MailChimp;
use Local\Validation\Validation;


//Load Composer's autoloader
require 'vendor/autoload.php';


//options parameter for user

$admin_email_to        = 'xyz@exampledomain.com';         // admin email who will get the contact email alert
$admin_email_to_name   = "Admin_Name";                    // Admin Name/Company name who will get the email alert
$admin_email_from      = 'noreply@exampledomain.com';     // admin email from which email address email will be sent
$admin_email_from_name = 'System';                        //admin name from which email will be sent
$admin_send_subject    = 'Contact form alert';            //email subject what the admin will get as contact email alert
$user_send_subject     = 'Thanks for contact, your copy'; //email subject what the user will get if the user agreed or select "copy me"

//end options parameter for user


$list               = [];
$validation_message = [
	'error'       => false,
	'validation_error'       => false,
	'error_field' => [],
	'message'     => []
];

$rules = [
	'cbxname'    => 'trim|required|alpha_spaces',
	'cbxemail'   => 'trim|required|email',
	'cbxmessage' => 'trim|required|alpha_numeric_spaces',
	'cbxsubject' => 'trim|required|alpha_numeric_spaces',
];

if ( $_POST ) {
	$frm_val = new Validation;

	foreach ( $rules as $post_key => $rule ) {
		$frm_val->validate( $post_key, $rule );
	}

	$validation_info             = $frm_val->validation_info();
	$validation_message['validation_error'] = ! $validation_info['validation'];

	foreach ( $validation_info['error_list'] as $error_field => $message ) {
		$validation_message['error_field'][]           = $error_field;
		$validation_message['message'][ $error_field ] = $message;
	}

	$cbxname    = $frm_val->get_value( 'cbxname' );
	$cbxemail   = $frm_val->get_value( 'cbxemail' );
	$cbxsendme  = isset( $_POST['cbxsendme'] ) ? 'on' : '';
	$cbxmessage = $frm_val->get_value( 'cbxmessage' );
	$cbxsubject = $frm_val->get_value( 'cbxsubject' );


	if ( $validation_info['validation'] ) {
		try {
			//Create an instance; passing `true` enables exceptions
			$mail = new PHPMailer( true );


			//some config if you need help based on your server configuration
			$mail->isSMTP();
			$mail->Host = '127.0.0.1';                             // Specify main and backup SMTP servers
			//$mail->SMTPAuth = true;
			//$mail->SMTPSecure = 'tls';                            // Enable TLS encryption, `ssl` also accepted
			$mail->Port = 1025;                                    // TCP port to connect to
			//$mail->Username = '';                 // SMTP username
			//$mail->Password = '';                    // SMTP password

			//add admin from email
			$mail->From = $admin_email_from;
			//add admin from name
			$mail->FromName = $admin_email_from_name;
			//add admin to email and name
			$mail->addAddress( $admin_email_to, $admin_email_to_name );

			//add more if you need more to recipient
			//$mail->addAddress('ellen@example.com');               // Name is optional

			//add if you need reply to
			//$mail->addReplyTo('', '');
			//add if you need cc
			//$mail->addCC('');

			//add if you need bcc
			// $mail->addBCC('');

			//$mail->addAttachment('');     // Add attachments
			//$mail->addAttachment('');    // Optional name
			$mail->isHTML( true );                                 // Set email format to HTML

			$mail->Subject = ( $cbxsubject == '' ) ? $admin_send_subject : $cbxsubject;
			$mail->Body    = $cbxmessage;
			//$mail->AltBody = 'This is the body in plain text for non-HTML mail clients';


			if ( $mail->send() === true ) {
				$validation_message['successmessage'] = 'Message has been sent successfully !';
			} else {

				$validation_message['error'] = true;
				$validation_message['successmessage'] = 'Sorry, Mail could not be sent. Please contact server admin.';
			}

			//send email to user if user agreed or selected "copy me"
			if ( $cbxsendme == 'on' ) {

				try {
					$mail2 = new PHPMailer;

					$mail2->isSMTP();
					//some config if you need help based on your server configuration
					$mail2->Host = '127.0.0.1';                              // Specify main and backup SMTP servers

					// $mail->Username = '';                 // SMTP username
					// $mail->Password = '';                           // SMTP password
					// $mail->SMTPSecure = '';                            // Enable TLS encryption, `ssl` also accepted
					$mail2->Port = 1025;                                     // TCP port to connect to

					//add admin from email
					$mail2->From = $admin_email_from;
					//add admin from name
					$mail2->FromName = $admin_email_from_name;
					//now send to user
					//$mail->From = $admin_email_from;
					// $mail->FromName = $admin_email_from_name;
					//$mail->all_recipients = array();
					$mail2->addAddress( $cbxemail, $cbxname );               // Add a recipient, user who fillted the contact form
					//$mail->addAddress('ellen@example.com');               // Name is optional
					//$mail->addReplyTo('info@example.com', 'Information');
					//$mail->addCC('cc@example.com');
					// $mail->addBCC('bcc@example.com');

					//$mail->addAttachment('/var/tmp/file.tar.gz');         // Add attachments
					//$mail->addAttachment('/tmp/image.jpg', 'new.jpg');    // Optional name
					$mail2->isHTML( true );                                  // Set email format to HTML

					$mail2->Subject = 'Copy Mail:' . $admin_send_subject;
					$mail2->Body    = $cbxmessage;
					//$mail->AltBody = 'This is the body in plain text for non-HTML mail clients';

					if ( $mail2->send() === true ) {
						//$validation_message['successmessage'] = 'Message has been sent successfully !';

					} else {
						//$validation_message['successmessage'] = 'Sorry, Mail could not be sent. Please contact server admin.';

					}
				} catch ( Exception $e ) {
					//echo "Message could not be sent. Mailer Error: {$mail->ErrorInfo}";
					//$validation_message['successmessage'] = "Message could not be sent. Mailer Error: {$mail->ErrorInfo}";
				}

			}
		} catch ( Exception $e ) {
			//echo "Message could not be sent. Mailer Error: {$mail->ErrorInfo}";
			$validation_message['error'] = true;
			$validation_message['successmessage'] = "Message could not be sent. Mailer Error: {$mail->ErrorInfo}";
		}
	}

	//end send email

	echo json_encode( $validation_message );
	die( 1 );
}
