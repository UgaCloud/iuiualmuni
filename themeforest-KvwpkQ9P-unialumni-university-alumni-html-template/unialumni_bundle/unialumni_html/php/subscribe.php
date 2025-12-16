<?php

use \DrewM\MailChimp\MailChimp;
use Local\Validation\Validation;


//Load Composer's autoloader
require 'vendor/autoload.php';


//mailchimp specifif
$api_key = ''; //set mailchimp api key
$list_id = '';                                      //set mailchimp list id


$validation_message = [
	'error'            => false,
	'validation_error' => false,
	'error_field'      => [],
	'message'          => []
];

$rules = [
	'email' => 'trim|required|email'
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

	//if validation passed
	if ( $validation_info['validation'] ) {

		if ( $api_key != '' && $list_id != '' ) {
			$mailchimp = new MailChimp($api_key);

			try {

				$result = $mailchimp->post("lists/$list_id/members", [
					'email_address' => $_POST['email'],
					'status'        => 'subscribed',
				]);

				$validation_message['successmessage'] = "Subscription success";

			} catch ( Exception $Exp ) {
				$validation_message['error'] = true;
				$validation_message['successmessage'] = "Subscription failed. Error: {$Exp->getMessage()}";
			}
		} else {
			$validation_message['error']   = true;
			$validation_message['successmessage'] = 'Api key or list id missing';
		}
	}

	echo json_encode( $validation_message );
	die( 1 );
}